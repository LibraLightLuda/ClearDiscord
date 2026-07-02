# -*- coding: utf-8 -*-
"""
Undiscord Python GUI
Discord 채널 내 특정 사용자가 작성한 메시지를 API를 사용하여 자동으로 삭제하는 GUI 도구입니다.
이 파일은 사용자 인터페이스(Tkinter) 구성, 비동기 스레딩, 설정 입출력 및 다국어 이벤트 제어를 전담합니다.
"""

import sys
import os
import json
import threading
import queue
import requests
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from tkinter.scrolledtext import ScrolledText

# 분리된 내부 모듈로부터 핵심 비즈니스 로직, 시스템 상태 검사 및 헬퍼 함수들을 가져옵니다.
from undiscord_utils import (
    ms_to_hms, 
    to_snowflake, 
    calculate_relative_date, 
    validate_discord_url,
    resource_path
)
from undiscord_crypto import encrypt_data, decrypt_data
from undiscord_layout import setup_styles, create_widgets, update_ui_texts
from undiscord_core import UndiscordCore, fetch_guilds, fetch_channels
from undiscord_dialogs import PasswordDialog
from undiscord_i18n import get_system_language, MESSAGES

# ==================================================
# 하위 호환성 (Re-export) 정의
# ==================================================
__all__ = ['UndiscordCore', 'PasswordDialog', 'to_snowflake', 'ms_to_hms']


def run_login_window():
    """pywebview를 사용하여 디스코드 로그인 페이지를 띄우고 토큰을 자동 추출합니다."""
    import time
    import threading
    import traceback
    import sys
    
    # 서브프로세스 내부의 모든 초기화 및 런타임 에러를 가로채 메인 프로세스로 리다이렉트합니다.
    try:
        try:
            import webview
        except ImportError:
            # pywebview 자동 설치 시도
            import subprocess
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview"])
                import webview
            except Exception as e:
                print(f"ERROR: pywebview installation failed. {e}\n{traceback.format_exc()}", flush=True)
                sys.exit(1)
        
        token_found = [None]
        
        # 디스코드 보안 차단(reCAPTCHA / Cloudflare) 우회를 위한 최신 Chrome 브라우저 User-Agent 위장
        try:
            webview.settings['USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        except Exception as e:
            print(f"DEBUG: Setting user agent failed: {e}", flush=True)
        
        def check_token(window):
            # 디스코드 웹 세션 토큰 추출을 위한 복합 JS (iframe LocalStorage 우회 및 Webpack Chunk 듀얼 감지)
            js_code = """
            (function() {
                try {
                    // 기법 1: iframe 생성을 통한 localStorage.token 우회 탈취
                    let iframe = document.createElement('iframe');
                    document.head.append(iframe);
                    let token = iframe.contentWindow.localStorage.token;
                    iframe.remove();
                    if (token) {
                        return token.replace(/"/g, '');
                    }
                } catch (e) {}
                
                try {
                    // 기법 2: Webpack Chunk Injection 방식
                    return (window.webpackChunkdiscord_app.push([
                        [Math.random()],
                        {},
                        (req) => {
                            for (const m of Object.keys(req.c).map((x) => req.c[x].exports)) {
                                if (m && m.default && m.default.getToken !== undefined) {
                                    return m.default.getToken();
                                }
                            }
                        }
                    ]));
                } catch (e) {}
                
                return null;
            })()
            """
            while True:
                try:
                    time.sleep(0.5)
                    res = window.evaluate_js(js_code)
                    if res and isinstance(res, str) and len(res.strip()) > 30:
                        token_found[0] = res.strip()
                        print(f"TOKEN:{token_found[0]}", flush=True)
                        window.destroy()
                        break
                except Exception as ex:
                    # 페이지 리다이렉션 중 일시적인 자바스크립트 실행 예외는 무시하고 감시를 유지합니다.
                    # 단, 창이 수동으로 완전히 닫힌 경우(Exception 메시지에 파괴/닫힘 관련 문구 포함 시) 감시 루프를 탈출합니다.
                    err_str = str(ex).lower()
                    if any(x in err_str for x in ['close', 'destroy', 'null', 'object', 'access', 'denied']):
                        break
                    continue

        # 반응형 레이아웃 대응 및 QR코드 로그인 영역이 숨겨지지 않도록 창 크기를 가로로 충분히 확장합니다. (width=1000)
        window = webview.create_window(
            title="Discord Easy Login",
            url="https://discord.com/login",
            width=1000,
            height=700,
            resizable=True
        )
        
        # 렌더러 로딩 완료 이전 evaluate_js 호출로 인한 교착 상태 및 프리징 방지를 위해 loaded 이벤트 시점에 스레드 구동
        def on_loaded():
            t = threading.Thread(target=check_token, args=(window,), daemon=True)
            t.start()
            
        window.events.loaded += on_loaded
        
        # pywebview의 기본 브라우저 시작 구동을 지시합니다. (기본 설정이 최적의 안정성을 보장합니다)
        webview.start()
        
    except Exception as e:
        print(f"ERROR: {e}\n{traceback.format_exc()}", flush=True)
        sys.exit(1)


class UndiscordGUIApp:
    """
    디스코드 스타일의 2x2 격자형 대시보드 레이아웃을 통해
    사용자가 언어를 전환하고 옵션을 제어하며 진행 로그를 실시간 모니터링하는 UI 애플리케이션입니다.
    """
    def __init__(self, root):
        self.root = root
        self.root.geometry("1120x860")
        self.root.minsize(1080, 800)
        
        # 타이틀바 및 작업표시줄 아이콘 설정 (PyInstaller 리소스 패키징 경로 추적)
        try:
            png_path = resource_path("cold.png")
            ico_path = resource_path("cold.ico")
            if os.path.exists(png_path):
                self.icon_img = tk.PhotoImage(file=png_path)
                self.root.iconphoto(False, self.icon_img)
            elif os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except Exception as e:
            print(f"아이콘 로딩 실패: {e}")
        
        self.log_queue = queue.Queue()
        self.engine = None
        self.engine_thread = None
        
        # 보안 토큰 암호화 세션 패스워드 캐싱 변수
        self.session_password = None
        self.guilds_map = {}
        self.channels_map = {}

        # 다국어(i18n) 설정 초기 감지 (기본값 설정)
        self.current_lang = get_system_language()

        # 디스코드 테마 칼라 설정
        self.bg_dark = "#202225"     # 프로그램 배경
        self.bg_panel = "#2f3136"    # 카드 프레임 배경
        self.bg_input = "#36393f"    # 입력창 배경
        self.fg_white = "#ffffff"    # 주 텍스트
        self.fg_gray = "#b9bbbe"     # 부가 설명 회색
        
        self.color_accent = "#5865f2" # 디스코드 로얄 블루
        self.color_danger = "#ed4245" # 에러/중지 빨강
        self.color_success = "#57f287"# 시작 초록

        # UI 스타일시트 및 레이아웃 생성
        self.setup_styles()
        self.create_widgets()
        
        # 메인 창을 초기에 완전히 숨겨 비밀번호 인증을 통과하기 전까지 보이지 않도록 함
        self.root.withdraw()
        
        # 로그 폴링 및 창 닫기 핸들러 바인딩
        self.root.after(100, self.poll_log_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_window)
        
        # 즉시 설정 및 비밀번호 검증 루틴 가동
        self.root.after(10, self.load_config)

    def setup_styles(self):
        """프로그램 전반에 적용할 ttk 스타일 및 다크 테마 설정을 정의합니다."""
        setup_styles(self)

    def create_widgets(self):
        """2x2 대시보드 레이아웃의 모든 프레임과 인터랙션 위젯을 생성 및 배치합니다."""
        create_widgets(self)

    def toggle_language(self):
        """한국어와 영어 설정을 서로 토글하고 UI 텍스트를 즉각 갱신합니다."""
        self.current_lang = 'en' if self.current_lang == 'ko' else 'ko'
        update_ui_texts(self)
        self.save_config()

    def save_config(self):
        """보안상 마스터 비밀번호로 암호화한 토큰을 포함한 위젯의 입력 상태를 config.json에 보존합니다."""
        token_plain = self.var_token.get().strip()
        enc_token = ""
        salt_val = ""
        verify_val = ""
        msg = MESSAGES[self.current_lang]

        if token_plain:
            # 세션 비밀번호가 없는 경우 비밀번호 신규 설정 대화창 유도
            if self.session_password is None:
                dlg = PasswordDialog(self.root, mode="set", lang=self.current_lang)
                if dlg.result is not None:
                    if dlg.result == "":
                        self.session_password = ""
                        self.write_log('warn', "비밀번호 설정 없이 평문으로 토큰을 저장합니다." if self.current_lang == 'ko' else "Saving token in plaintext without password setup.")
                    elif len(dlg.result) < 8:
                        messagebox.showerror(msg['pass_err_title'], msg['pass_len_error'])
                        self.session_password = ""
                    else:
                        self.session_password = dlg.result
                else:
                    self.write_log('warn', msg['pass_token_skip_warn'])
                    self.session_password = ""
            
            update_ui_texts(self)
            
            if self.session_password:
                try:
                    enc_token, salt_val, verify_val = encrypt_data(token_plain, self.session_password)
                except Exception as e:
                    self.write_log('error', msg['pass_crypt_err'].format(e=e))

        config_data = {
            'guildId': self.var_guild_id.get(),
            'channelId': self.var_channel_id.get(),
            'authorId': self.var_author_id.get(),
            'minRange': self.var_min_range.get(),
            'maxRange': self.var_max_range.get(),
            'minQuickSelect': self.combo_min_quick.current(),
            'maxQuickSelect': self.combo_max_quick.current(),
            'searchText': self.var_search_text.get(),
            'pattern': self.var_pattern.get(),
            'hasLink': self.var_has_link.get(),
            'hasFile': self.var_has_file.get(),
            'includeNsfw': self.var_include_nsfw.get(),
            'includePinned': self.var_include_pinned.get(),
            'searchDelay': self.var_search_delay.get(),
            'minDelay': self.var_min_delay.get(),
            'maxDelay': self.var_max_delay.get(),
            'language': self.current_lang,
            # 암호화 관련 파라미터 직렬화 보관
            'encryptedToken': enc_token,
            'salt': salt_val,
            'verification': verify_val,
            'token': token_plain if not self.session_password else ""
        }
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            try:
                self.write_log('warn', msg['pass_config_err'].format(e=e))
            except Exception:
                pass

    def load_config(self):
        """로컬 config.json 파일로부터 위젯 복구 및 저장된 암호화 토큰 복구를 위한 다이얼로그를 구동합니다."""
        # 1. 이용약관 및 사용자 면책 동의(Disclaimer) 선제 수락 확인
        temp_lang = get_system_language()
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if 'language' in cfg:
                        temp_lang = cfg['language']
            except Exception:
                pass
        
        msg = MESSAGES[temp_lang]
        # 동의하지 않고 닫거나 거부하면 프로그램 즉시 종료
        if not messagebox.askyesno(msg['disclaimer_title'], msg['disclaimer_msg']):
            self.root.destroy()
            return

        data = {}
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"설정 로드 중 오류: {e}")
            
        # 언어 설정 복원 및 UI 텍스트 동적 갱신
        if 'language' in data:
            self.current_lang = data['language']
        update_ui_texts(self)
        
        msg = MESSAGES[self.current_lang]
        
        if 'guildId' in data: self.var_guild_id.set(data['guildId'])
        if 'channelId' in data: self.var_channel_id.set(data['channelId'])
        if 'authorId' in data: self.var_author_id.set(data['authorId'])
        
        # 퀵 셀렉트 콤보박스 설정 먼저 로드
        if 'minQuickSelect' in data:
            try:
                self.combo_min_quick.current(data['minQuickSelect'])
            except Exception:
                pass
        if 'maxQuickSelect' in data:
            try:
                self.combo_max_quick.current(data['maxQuickSelect'])
            except Exception:
                pass

        # 퀵 셀렉트 설정에 따라 현재 시간 기준으로 자동 갱신. "직접 입력"인 경우에는 저장된 이전 값을 복구
        min_sel = self.combo_min_quick.get()
        manual_str = msg['quick_options'][0]
        if min_sel and min_sel != manual_str:
            self.var_min_range.set(calculate_relative_date(min_sel))
        elif 'minRange' in data:
            self.var_min_range.set(data['minRange'])

        max_sel = self.combo_max_quick.get()
        if max_sel and max_sel != manual_str:
            self.var_max_range.set(calculate_relative_date(max_sel))
        elif 'maxRange' in data:
            self.var_max_range.set(data['maxRange'])

        if 'searchText' in data: self.var_search_text.set(data['searchText'])
        if 'pattern' in data: self.var_pattern.set(data['pattern'])
        
        if 'hasLink' in data: self.var_has_link.set(data['hasLink'])
        if 'hasFile' in data: self.var_has_file.set(data['hasFile'])
        if 'includeNsfw' in data: self.var_include_nsfw.set(data['includeNsfw'])
        if 'includePinned' in data: self.var_include_pinned.set(data['includePinned'])

        if 'searchDelay' in data: self.var_search_delay.set(data['searchDelay'])
        if 'minDelay' in data: self.var_min_delay.set(data['minDelay'])
        if 'maxDelay' in data: self.var_max_delay.set(data['maxDelay'])

        # 암호화된 토큰 로드 시도 및 비밀번호 질문 처리
        enc_token = data.get('encryptedToken', '')
        salt_str = data.get('salt', '')
        verify_str = data.get('verification', '')
        plain_token = data.get('token', '')

        if enc_token and salt_str and verify_str:
            self.var_token.set("")  # 패스워드 검증 전까지 공란 처리
            attempts = 0
            max_attempts = 3
            success = False

            while attempts < max_attempts:
                dlg = PasswordDialog(self.root, mode="enter", lang=self.current_lang)
                if not dlg.result:
                    self.write_log('warn', msg['pass_cancel_warn'])
                    break

                try:
                    decrypted = decrypt_data(enc_token, dlg.result, salt_str, verify_str)
                    self.var_token.set(decrypted)
                    self.session_password = dlg.result
                    self.write_log('success', msg['pass_verify_success'])
                    success = True
                    break
                except ValueError:
                    attempts += 1
                    left = max_attempts - attempts
                    if left > 0:
                        messagebox.showerror(msg['pass_err_title'], msg['pass_verify_fail_fmt'].format(left=left))
                    else:
                        # 3회 연속 오답 시 로컬 보안 보호를 위해 저장 데이터 파괴
                        messagebox.showerror(msg['pass_destroy_title'], msg['pass_destroy_msg'])
                        self.session_password = None
                        self.var_token.set("")
                        
                        # JSON 설정 파일 갱신 기록
                        data['encryptedToken'] = ""
                        data['salt'] = ""
                        data['verification'] = ""
                        data['token'] = ""
                        try:
                            with open("config.json", "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=4, ensure_ascii=False)
                            self.write_log('error', msg['log_pass_destroy'])
                        except Exception as ex:
                            self.write_log('error', msg['log_pass_destroy_err'].format(ex=ex))
                        break
            
            if success:
                update_ui_texts(self)
                # 비밀번호 검증 성공 시에만 메인 창 노출
                self.root.deiconify()
            else:
                # 취소 또는 3회 실패 시 즉각 프로그램 파괴/완전 종료
                # 3회 연속 실패한 경우에만 에러 박스를 띄움
                if attempts >= max_attempts:
                    messagebox.showerror(msg['err_title'], msg['pass_block_err'])
                self.root.destroy()
                return
        elif plain_token:
            # 평문 토큰이 이미 저장되어 있는 경우 바로 로드
            self.var_token.set(plain_token)
            self.session_password = ""
            self.write_log('success', "저장된 평문 토큰을 성공적으로 로드했습니다." if self.current_lang == 'ko' else "Successfully loaded the stored plaintext token.")
            update_ui_texts(self)
            self.root.deiconify()
        else:
            # 최초 실행 등으로 인해 비밀번호 정보가 아예 저장되지 않은 경우 실행 시 우선 설정하도록 강제
            self.write_log('info', msg['log_pass_no_exist'])
            dlg = PasswordDialog(self.root, mode="set", lang=self.current_lang)
            if dlg.result is not None:
                if dlg.result == "":
                    self.session_password = ""
                    self.write_log('success', "비밀번호 설정 없이 평문으로 저장되도록 시작합니다." if self.current_lang == 'ko' else "Started without password. Tokens will be saved in plaintext.")
                    self.save_config()
                    self.root.deiconify()
                elif len(dlg.result) < 8:
                    messagebox.showerror(msg['pass_err_title'], msg['pass_len_error_exit'].replace("종료합니다", "평문 모드로 진행합니다").replace("Aborting execution", "Proceeding in plaintext mode"))
                    self.session_password = ""
                    self.save_config()
                    self.root.deiconify()
                else:
                    self.session_password = dlg.result
                    self.write_log('success', msg['log_pass_init_ok'])
                    self.save_config()
                    # 설정 성공했으므로 메인 창 노출
                    self.root.deiconify()
            else:
                self.write_log('warn', msg['pass_cancel_exit'])
                self.root.destroy()
                return

    def on_min_quick_select(self, event):
        sel = self.combo_min_quick.get()
        msg = MESSAGES[self.current_lang]
        if sel and sel != msg['quick_options'][0]:
            val = calculate_relative_date(sel)
            self.var_min_range.set(val)

    def on_max_quick_select(self, event):
        sel = self.combo_max_quick.get()
        msg = MESSAGES[self.current_lang]
        if sel and sel != msg['quick_options'][0]:
            val = calculate_relative_date(sel)
            self.var_max_range.set(val)

    def on_token_focus_out(self, event=None):
        token_plain = self.var_token.get().strip()
        msg = MESSAGES[self.current_lang]
        if not token_plain:
            return
        if self.session_password is not None:
            return

        dlg = PasswordDialog(self.root, mode="set", lang=self.current_lang)
        if dlg.result is not None:
            if dlg.result == "":
                self.session_password = ""
                self.write_log('warn', "비밀번호 설정 없이 평문으로 토큰을 저장합니다." if self.current_lang == 'ko' else "Saving token in plaintext without password setup.")
                self.save_config()
            elif len(dlg.result) < 8:
                messagebox.showerror(msg['pass_err_title'], msg['pass_len_error'])
                self.session_password = ""
                self.save_config()
            else:
                self.session_password = dlg.result
                self.write_log('success', msg['log_pass_init_ok'])
                self.save_config()
        else:
            self.write_log('warn', msg['pass_cancel_warn'])
            self.session_password = ""
            self.save_config()

    def toggle_token_visibility(self):
        msg = MESSAGES[self.current_lang]
        if self.entry_token.cget("show") == "*":
            self.entry_token.configure(show="")
            self.btn_toggle_token.configure(text=msg['btn_hide'])
        else:
            self.entry_token.configure(show="*")
            self.btn_toggle_token.configure(text=msg['btn_view'])

    def launch_auto_login(self):
        """간편 로그인 서브프로세스를 기동하여 토큰 자동 입력을 수행합니다."""
        threading.Thread(target=self._auto_login_thread_func, daemon=True).start()

    def _auto_login_thread_func(self):
        msg = MESSAGES[self.current_lang]
        import traceback
        import subprocess
        
        self.write_log('info', "[System LOG] 1단계: 간편 로그인 기동 스레드 시작")
        
        # pywebview 모듈 임포트 가능성 선제 검사 및 무소음 설치 유도
        try:
            self.write_log('info', "[System LOG] 2단계: 로컬 환경 pywebview 설치 체크...")
            import webview
            self.write_log('success', "[System LOG] pywebview 모듈 감지됨.")
        except ImportError:
            self.write_log('info', msg['err_easy_login_install'])
            try:
                startupinfo = None
                if sys.platform == 'win32':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                # 메인 UI가 뜬 상태이므로 로그에 문구를 남기고 백그라운드 스레드에서 직접 설치를 진행합니다.
                self.write_log('info', "[System LOG] pip install pywebview 명령 실행...")
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "pywebview"],
                    startupinfo=startupinfo
                )
                self.write_log('success', "성공적으로 필수 라이브러리(pywebview)가 설치되었습니다. 로그인을 기동합니다." if self.current_lang == 'ko' else "Successfully installed pywebview! Launching login window.")
            except Exception as e:
                err_trace = traceback.format_exc()
                self.write_log('error', f"필수 라이브러리 설치 실패: {e}\n{err_trace}")
                return

        # 본래의 간편 로그인 서브프로세스 기동
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable, "--login"]
        else:
            # sys.argv[0] 대신 실제 모듈의 절대 경로(__file__)를 명시적으로 기입하여 실행 안정성을 확보합니다.
            script_path = os.path.abspath(__file__)
            cmd = [sys.executable, script_path, "--login"]
            
        self.write_log('info', f"[System LOG] 3단계: 서브프로세스 커맨드 구성 완료: {cmd}")
        self.write_log('info', msg['log_easy_login_start'])
        
        try:
            creationflags = 0
            if sys.platform == 'win32':
                # STARTF_USESHOWWINDOW를 사용하면 자식 프로세스의 GUI 윈도우까지 SW_HIDE 상태로 숨겨집니다.
                # 대신 CREATE_NO_WINDOW를 적용하여 콘솔창만 숨기고 로그인 웹뷰 창은 정상 노출되도록 보장합니다.
                creationflags = subprocess.CREATE_NO_WINDOW
                
            self.write_log('info', "[System LOG] 4단계: Popen 서브프로세스 팝업 시작...")
            # 교착 상태(Deadlock)를 방지하기 위해 stderr를 stdout으로 묶어서(STDOUT) 단일 파이프 스트림으로 관리합니다.
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                creationflags=creationflags
            )
            self.write_log('info', f"[System LOG] 서브프로세스 기동 성공. PID: {proc.pid}")
            
            token = None
            error_msg = None
            full_output = []
            
            self.write_log('info', "[System LOG] 5단계: 표준 출력 스트림 실시간 폴링 중...")
            # 실시간으로 출력을 전부 읽으며 버퍼 포화를 예방합니다.
            for line in iter(proc.stdout.readline, ''):
                full_output.append(line)
                if line.startswith("TOKEN:"):
                    token = line.strip().split("TOKEN:")[1]
                    break
                elif line.startswith("ERROR:"):
                    error_msg = line.strip()
            
            # 남은 스트림 비우기 및 자식 프로세스 완전 종료 대기
            proc.wait()
            self.write_log('info', f"[System LOG] 6단계: 서브프로세스 종료됨. Exit Code: {proc.returncode}")
            
            if token:
                self.root.after(0, lambda: self.set_extracted_token(token))
            else:
                raw_log = "".join(full_output).strip()
                if error_msg or raw_log:
                    # 모든 에러 정보와 서브프로세스 출력 스택 트레이스를 로그창에 직접 출력
                    self.write_log('error', f"[Subprocess Log]\n{error_msg or raw_log}")
                self.write_log('warn', msg['log_easy_login_cancel'])
                
        except Exception as e:
            err_trace = traceback.format_exc()
            self.write_log('error', msg['log_easy_login_err'].format(e=e))
            self.write_log('error', f"[Traceback Log]\n{err_trace}")
            self.root.after(0, lambda: messagebox.showerror(msg['err_title'], msg['log_easy_login_err'].format(e=e)))

    def set_extracted_token(self, token):
        """추출된 토큰을 복원 입력하고 마스터 비밀번호 저장을 트리거합니다."""
        msg = MESSAGES[self.current_lang]
        self.var_token.set(token)
        self.write_log('success', msg['log_easy_login_success'])
        messagebox.showinfo(msg['ok'], msg['log_easy_login_success'])
        self.on_token_focus_out()  # 토큰 세션 암호화 저장 트리거

    def click_clear_log(self):
        self.log_area.delete("1.0", tk.END)

    def write_log(self, log_type, text):
        now_time = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{now_time}] "
        self.log_area.insert(tk.END, prefix, 'verb')
        self.log_area.insert(tk.END, text + "\n", log_type)
        self.log_area.see(tk.END)

    def click_start(self):
        self.save_config()
        msg = MESSAGES[self.current_lang]

        try:
            search_delay = self.var_search_delay.get()
            min_delay = self.var_min_delay.get()
            max_delay = self.var_max_delay.get()
            
            if search_delay < 0 or min_delay < 0 or max_delay < 0:
                raise ValueError()
        except (tk.TclError, ValueError):
            messagebox.showerror(msg['err_title'], msg['err_delay_number'])
            return

        token = self.var_token.get().strip()
        guild_id = self.var_guild_id.get().strip()
        channel_raw = self.var_channel_id.get().strip()

        if not token:
            messagebox.showerror(msg['err_title'], msg['err_token_empty'])
            return
        if not guild_id:
            messagebox.showerror(msg['err_title'], msg['err_guild_empty'])
            return
        if not channel_raw:
            messagebox.showerror(msg['err_title'], msg['err_channel_empty'])
            return

        # 작성자 ID가 비어있고 토큰이 있는 경우, 본인 계정 ID 조회하여 자동 기입
        author_id_input = self.var_author_id.get().strip()
        if not author_id_input:
            if token:
                self.write_log('info', msg['log_search_author'])
                try:
                    url = "https://discord.com/api/v9/users/@me"
                    validate_discord_url(url)
                    resp = requests.get(
                        url, 
                        headers={'Authorization': token}, 
                        timeout=5, 
                        proxies={'http': None, 'https': None}, 
                        verify=True
                    )
                    if resp.ok:
                        me_data = resp.json()
                        my_id = me_data.get("id")
                        if my_id:
                            self.var_author_id.set(my_id)
                            author_id_input = my_id
                            self.write_log('success', msg['log_author_auto_set'].format(my_id=author_id_input))
                            self.save_config()
                    else:
                        self.write_log('warn', msg['log_author_fail'].format(status=resp.status_code))
                except Exception as e:
                    self.write_log('warn', msg['log_author_net_err'].format(e=e))

        channel_ids = [ch.strip() for ch in channel_raw.split(',') if ch.strip()]

        options = {
            'authToken': token,
            'authorId': author_id_input or None,
            'guildId': guild_id,
            'channelId': channel_ids[0] if len(channel_ids) == 1 else None,
            'minId': self.var_min_range.get().strip() or None,
            'maxId': self.var_max_range.get().strip() or None,
            'content': self.var_search_text.get().strip() or None,
            'pattern': self.var_pattern.get().strip() or None,
            'hasLink': self.var_has_link.get(),
            'hasFile': self.var_has_file.get(),
            'includeNsfw': self.var_include_nsfw.get(),
            'includePinned': self.var_include_pinned.get(),
            'searchDelay': search_delay,
            'useRandomDelay': True,
            'minDeleteDelay': min_delay,
            'maxDeleteDelay': max_delay,
            'maxAttempt': 2,
            'askForConfirmation': True,
            'ask_callback': self.ask_confirmation_callback,
            'language': self.current_lang
        }

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_bar.configure(value=0)
        self.click_clear_log()

        self.engine = UndiscordCore(
            options=options,
            log_queue=self.log_queue,
            progress_callback=self.update_progress_callback,
            stop_callback=self.engine_stopped_callback
        )

        if len(channel_ids) > 1:
            jobs = [{'guildId': guild_id, 'channelId': ch} for ch in channel_ids]
            self.engine_thread = threading.Thread(target=self.engine.run_batch, args=(jobs,), daemon=True)
        else:
            self.engine_thread = threading.Thread(target=self.engine.run, daemon=True)

        self.engine_thread.start()

    def click_stop(self):
        msg = MESSAGES[self.current_lang]
        if self.engine:
            self.engine.stop()
            self.write_log('warn', msg['log_stop_cmd'])
            self.btn_stop.configure(state="disabled")

    def on_close_window(self):
        self.save_config()
        msg = MESSAGES[self.current_lang]
        if self.engine and self.engine.state['running']:
            if messagebox.askyesno(msg['confirm_exit_title'], msg['confirm_exit_msg']):
                self.engine.stop()
                self.root.after(300, self.root.destroy)
        else:
            self.root.destroy()

    def show_help_window(self):
        """디스코드 인증키(토큰) 및 ID 식별자 획득 방법을 안내하는 고해상도 도움말 탭 윈도우를 구동합니다."""
        msg = MESSAGES[self.current_lang]
        help_win = tk.Toplevel(self.root)
        help_win.title(msg['btn_help'])
        help_win.geometry("640x560")
        help_win.resizable(False, False)
        help_win.configure(bg=self.bg_panel)
        
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        help_win.geometry(f"+{main_x + 80}+{main_y + 80}")
        
        lbl_title = tk.Label(
            help_win, 
            text=msg['help_title'], 
            font=("Malgun Gothic", 12, "bold"), 
            fg=self.color_accent, 
            bg=self.bg_panel
        )
        lbl_title.pack(anchor="w", padx=20, pady=(15, 10))

        notebook = ttk.Notebook(help_win, style='Help.TNotebook')
        notebook.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # ---- 탭 1: 인증 토큰 찾기 ----
        tab1 = ttk.Frame(notebook, style='Card.TFrame')
        notebook.add(tab1, text=msg['help_tab1'])

        txt_token = ScrolledText(
            tab1, 
            bg=self.bg_input, 
            fg=self.fg_white, 
            insertbackground=self.fg_white, 
            font=("Malgun Gothic", 10), 
            bd=0, 
            wrap="word", 
            padx=10, 
            pady=10
        )
        txt_token.pack(fill="both", expand=True)
        txt_token.insert(tk.END, msg['help_text_token'])
        txt_token.bind("<Key>", lambda e: "break")

        # ---- 탭 2: 서버 및 채널 ID 찾기 ----
        tab2 = ttk.Frame(notebook, style='Card.TFrame')
        notebook.add(tab2, text=msg['help_tab2'])

        txt_ids = ScrolledText(
            tab2, 
            bg=self.bg_input, 
            fg=self.fg_white, 
            insertbackground=self.fg_white, 
            font=("Malgun Gothic", 10), 
            bd=0, 
            wrap="word", 
            padx=10, 
            pady=10
        )
        txt_ids.pack(fill="both", expand=True)
        txt_ids.insert(tk.END, msg['help_text_ids'])
        txt_ids.bind("<Key>", lambda e: "break")

        # ---- 탭 3: 날짜 범위 및 필터 활용법 ----
        tab3 = ttk.Frame(notebook, style='Card.TFrame')
        notebook.add(tab3, text=msg['help_tab3'])

        txt_filters = ScrolledText(
            tab3, 
            bg=self.bg_input, 
            fg=self.fg_white, 
            insertbackground=self.fg_white, 
            font=("Malgun Gothic", 10), 
            bd=0, 
            wrap="word", 
            padx=10, 
            pady=10
        )
        txt_filters.pack(fill="both", expand=True)
        txt_filters.insert(tk.END, msg['help_text_filters'])
        txt_filters.bind("<Key>", lambda e: "break")

    # ----------------------------------------------------
    # 다중 스레드 연동 & 콜백
    # ----------------------------------------------------

    def ask_confirmation_callback(self, message):
        msg = MESSAGES[self.current_lang]
        return messagebox.askyesno(msg['confirm_start_title'], message)

    def update_progress_callback(self, state, stats):
        self.log_queue.put(('PROGRESS_UPDATE', (state.copy(), stats.copy())))

    def engine_stopped_callback(self, state, stats):
        self.log_queue.put(('ENGINE_STOPPED', (state.copy(), stats.copy())))

    def poll_log_queue(self):
        """엔진으로부터 수신되는 로그 데이터를 Tkinter 메인 루프에서 주기적으로 폴링하여 UI를 갱신합니다."""
        msg = MESSAGES[self.current_lang]
        try:
            while True:
                item = self.log_queue.get_nowait()
                msg_type = item[0]
                
                if msg_type == 'PROGRESS_UPDATE':
                    state, stats = item[1]
                    self.update_progress_ui(state, stats)
                elif msg_type == 'ENGINE_STOPPED':
                    state, stats = item[1]
                    self.btn_start.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    self.var_progress_status.set(
                        msg['progress_finished_fmt'].format(
                            del_count=state['delCount'], 
                            fail_count=state['failCount']
                        )
                    )
                    self.progress_bar.configure(value=state['delCount'] + state['failCount'])
                else:
                    text = item[1]
                    self.write_log(msg_type, text)
                    
                self.log_queue.task_done()
        except queue.Empty:
            pass
        
        self.root.after(100, self.poll_log_queue)

    def update_progress_ui(self, state, stats):
        """엔진 진행 데이터를 바탕으로 프로그레스바 및 레이블 상태 문자열을 갱신합니다."""
        val = state['delCount'] + state['failCount']
        total = max(state['grandTotal'], val, 1)
        msg = MESSAGES[self.current_lang]

        self.progress_bar.configure(maximum=total, value=val)

        elapsed = int((datetime.now() - stats['startTime']).total_seconds() * 1000)
        remaining = stats['etr']
        
        percent = int((val / total) * 100)
        status_msg = msg['progress_status_fmt'].format(
            percent=percent,
            val=val,
            total=total,
            del_count=state['delCount'],
            fail_count=state['failCount'],
            elapsed=ms_to_hms(elapsed),
            remaining=ms_to_hms(remaining)
        )
        self.var_progress_status.set(status_msg)

    def load_guilds_async(self):
        """서버 목록 조회를 위해 비동기 백그라운드 스레드를 기동합니다."""
        token = self.var_token.get().strip()
        msg = MESSAGES[self.current_lang]
        if not token:
            self.write_log('warn', msg['err_token_required_for_fetch'])
            messagebox.showwarning(msg['err_title'], msg['err_token_required_for_fetch'])
            return

        self.btn_load_guilds.configure(state="disabled")
        self.combo_guilds.configure(values=["Loading..."])
        self.combo_guilds.set("Loading...")
        self.write_log('info', msg['log_fetch_guilds_start'])

        threading.Thread(target=self._load_guilds_worker, args=(token,), daemon=True).start()

    def _load_guilds_worker(self, token):
        """실제 API 연동을 수행하는 워커 스레드 함수입니다."""
        try:
            guilds = fetch_guilds(token)
            self.root.after(0, self._load_guilds_success, guilds)
        except Exception as e:
            self.root.after(0, self._load_guilds_fail, str(e))

    def _load_guilds_success(self, guilds):
        """서버 목록 로드에 성공했을 때 UI를 갱신합니다."""
        msg = MESSAGES[self.current_lang]
        self.btn_load_guilds.configure(state="normal")
        self.write_log('success', msg['log_fetch_guilds_success'].format(count=len(guilds)))

        # 콤보박스에 표시할 리스트 구성
        # 첫 번째 항목으로 "개인 DM (@me)" 추가
        values = [msg['dm_display_name']]
        self.guilds_map = {"@me": msg['dm_display_name']}
        
        for g in guilds:
            name = g.get('name', 'Unknown Guild')
            g_id = g.get('id', '')
            display_name = f"{name} ({g_id})"
            values.append(display_name)
            self.guilds_map[g_id] = display_name
            self.guilds_map[display_name] = g_id

        self.combo_guilds.configure(values=values)
        self.combo_guilds.current(0)
        
        # 기본적으로 첫 번째(DM) 선택 유도
        self.on_guild_combo_select(None)

    def _load_guilds_fail(self, err_msg):
        """서버 목록 로드에 실패했을 때 UI 상태를 복구하고 오류 로그를 띄웁니다."""
        msg = MESSAGES[self.current_lang]
        self.btn_load_guilds.configure(state="normal")
        self.combo_guilds.configure(values=[msg['combo_guild_placeholder']])
        self.combo_guilds.set(msg['combo_guild_placeholder'])
        self.write_log('error', msg['err_fetch_failed'].format(e=err_msg))
        messagebox.showerror(msg['err_title'], msg['err_fetch_failed'].format(e=err_msg))

    def on_guild_combo_select(self, event):
        """서버 콤보박스 선택 시 호출되는 이벤트 핸들러입니다."""
        msg = MESSAGES[self.current_lang]
        val = self.combo_guilds.get()
        if val == msg['combo_guild_placeholder'] or val == "Loading...":
            return

        if val == msg['dm_display_name']:
            guild_id = "@me"
        else:
            guild_id = self.guilds_map.get(val, "")
        
        if not guild_id:
            return

        self.var_guild_id.set(guild_id)
        self.load_channels_async(guild_id)

    def load_channels_async(self, guild_id):
        """서버 ID에 귀속된 채널 목록 조회를 위해 비동기 백그라운드 스레드를 기동합니다."""
        token = self.var_token.get().strip()
        msg = MESSAGES[self.current_lang]
        if not token:
            return

        self.combo_channels.configure(values=["Loading..."])
        self.combo_channels.set("Loading...")

        threading.Thread(target=self._load_channels_worker, args=(token, guild_id), daemon=True).start()

    def _load_channels_worker(self, token, guild_id):
        """채널 목록 API 호출을 진행하는 워커 스레드 함수입니다."""
        try:
            channels = fetch_channels(token, guild_id)
            self.root.after(0, self._load_channels_success, channels, guild_id)
        except Exception as e:
            self.root.after(0, self._load_channels_fail, str(e))

    def _load_channels_success(self, channels, guild_id):
        """채널 목록 로딩 성공 시 UI 갱신을 진행합니다."""
        msg = MESSAGES[self.current_lang]
        self.write_log('success', msg['log_fetch_channels_success'].format(count=len(channels)))

        values = []
        self.channels_map = {}

        if guild_id == "@me":
            # 개인 DM 채널들
            for c in channels:
                c_id = c.get('id', '')
                c_type = c.get('type', 1)
                
                # recipients 파싱
                recipients = c.get('recipients', [])
                if recipients:
                    user_names = []
                    for r in recipients:
                        g_name = r.get('global_name')
                        u_name = r.get('username', 'Unknown')
                        if g_name and g_name != u_name:
                            user_names.append(f"{g_name} ({u_name})")
                        else:
                            user_names.append(u_name)
                    names = ", ".join(user_names)
                else:
                    names = c.get('name', 'Group DM')
                    
                display_name = f"👤 {names} ({c_id})" if c_type == 1 else f"👥 {names} ({c_id})"
                values.append(display_name)
                self.channels_map[display_name] = c_id
        else:
            # 일반 서버 채널들 (카테고리 type 4는 제외)
            filtered_channels = [c for c in channels if c.get('type') != 4]
            for c in filtered_channels:
                c_id = c.get('id', '')
                c_name = c.get('name', 'unknown')
                c_type = c.get('type', 0)
                
                prefix = "#"
                if c_type == 2:
                    prefix = "🔊"
                elif c_type in [11, 12]:
                    prefix = "🧵"
                    
                display_name = f"{prefix} {c_name} ({c_id})"
                values.append(display_name)
                self.channels_map[display_name] = c_id

        if not values:
            values = [msg['combo_channel_placeholder']]
            self.combo_channels.configure(values=values)
            self.combo_channels.set(msg['combo_channel_placeholder'])
        else:
            self.combo_channels.configure(values=values)
            self.combo_channels.current(0)
            self.on_channel_combo_select(None)

    def _load_channels_fail(self, err_msg):
        """채널 목록 로딩 실패 시 UI 복구 및 오류 출력합니다."""
        msg = MESSAGES[self.current_lang]
        self.combo_channels.configure(values=[msg['combo_channel_placeholder']])
        self.combo_channels.set(msg['combo_channel_placeholder'])
        self.write_log('error', msg['err_fetch_failed'].format(e=err_msg))

    def on_channel_combo_select(self, event):
        """채널 콤보박스 선택 시 호출되는 이벤트 핸들러입니다."""
        val = self.combo_channels.get()
        if not val or not hasattr(self, 'channels_map'):
            return
        
        channel_id = self.channels_map.get(val, "")
        if channel_id:
            self.var_channel_id.set(channel_id)


# ==========================================
# 엔트리 포인트
# ==========================================

if __name__ == "__main__":
    if sys.platform == 'win32':
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except Exception:
            pass

    # 간편 로그인 모듈 기동 인자 검증
    if len(sys.argv) > 1 and sys.argv[1] == '--login':
        run_login_window()
        sys.exit(0)

    try:
        import ctypes
        # Windows OS 고해상도 DPI 환경 대응
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        
        # Windows에서 파이썬 기본 아이콘 대신 지정한 아이콘(cold.png)이 작업표시줄에 뜨도록 설정
        myappid = 'libralight.undiscord.gui.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    root = tk.Tk()
    app = UndiscordGUIApp(root)
    root.mainloop()

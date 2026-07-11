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
from undiscord_crypto import (
    encrypt_data, 
    decrypt_data,
    encrypt_ipc,
    decrypt_ipc,
    wipe_memory_string
)
from undiscord_layout import setup_styles, create_widgets, update_ui_texts
from undiscord_core import UndiscordCore
from undiscord_client import fetch_guilds, fetch_channels
from undiscord_dialogs import PasswordDialog
from undiscord_i18n import get_system_language, MESSAGES

# ==================================================
# 하위 호환성 (Re-export) 정의
# ==================================================
__all__ = ['UndiscordCore', 'PasswordDialog', 'to_snowflake', 'ms_to_hms']





class UndiscordGUIApp:
    """
    디스코드 스타일의 2x2 격자형 대시보드 레이아웃을 통해
    사용자가 언어를 전환하고 옵션을 제어하며 진행 로그를 실시간 모니터링하는 UI 애플리케이션입니다.
    """
    def __init__(self, root):
        self.root = root
        
        # 메인 윈도우 스타일링 및 위젯 레이아웃 구성 도중 화면 깜빡임(잠깐 떴다 사라짐) 현상을
        # 원천 방어하기 위해 초기화 진입 즉시 화면 상에서 완전히 보이지 않도록 숨깁니다.
        self.root.withdraw()
        
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
        
        # (초기화 최상단에서 선제 숨김 처리 완료)
        
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
        from undiscord_config import save_config
        save_config(self)

    def load_config(self):
        """로컬 config.json 파일로부터 위젯 복구 및 저장된 암호화 토큰 복구를 위한 다이얼로그를 구동합니다."""
        from undiscord_config import load_config
        load_config(self)

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

        # IPC 통신용 일회용 임시 대칭키 및 IV를 안전하게 생성합니다. (32바이트 AES 키)
        import secrets
        import os
        ephemeral_key = secrets.token_hex(32)
        
        # 본래의 간편 로그인 서브프로세스 기동
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable, "--login"]
        else:
            # sys.argv[0] 대신 실제 모듈의 절대 경로(__file__)를 명시적으로 기입하여 실행 안정성을 확보합니다.
            script_path = os.path.abspath(__file__)
            cmd = [sys.executable, script_path, "--login"]
            
        # 서브프로세스 환경 복사 및 일회용 비밀 키 주입
        child_env = os.environ.copy()
        child_env["ENV_SEC_KEY"] = ephemeral_key
        
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
                creationflags=creationflags,
                env=child_env  # 환경변수로 일회용 키 주입
            )
            self.write_log('info', f"[System LOG] 서브프로세스 기동 성공. PID: {proc.pid}")
            
            token = None
            error_msg = None
            full_output = []
            
            self.write_log('info', "[System LOG] 5단계: 표준 출력 스트림 실시간 폴링 중...")
            # 실시간으로 출력을 전부 읽으며 버퍼 포화를 예방합니다.
            for line in iter(proc.stdout.readline, ''):
                full_output.append(line)
                if line.startswith("TOKEN_ENC:"):
                    enc_val = line.strip().split("TOKEN_ENC:")[1]
                    try:
                        # 부모 측에서 일회성 키로 복호화
                        token = decrypt_ipc(enc_val, ephemeral_key)
                    except Exception as e:
                        error_msg = f"ERROR: IPC decryption failed: {e}"
                    break
                elif line.startswith("TOKEN:"):
                    # 평문 폴백 (하위 호환)
                    token = line.strip().split("TOKEN:")[1]
                    break
                elif line.startswith("ERROR:"):
                    error_msg = line.strip()
            
            # 사용 후 즉시 일회성 키 소거
            try:
                wipe_memory_string(ephemeral_key)
            except Exception:
                pass
            
            # 남은 스트림 비우기 및 자식 프로세스 완전 종료 대기
            proc.wait()
            self.write_log('info', f"[System LOG] 6단계: 서브프로세스 종료됨. Exit Code: {proc.returncode}")
            
            if token:
                self.root.after(0, lambda: self.set_extracted_token(token))
            else:
                raw_log = "".join(full_output).strip()
                
                # 단순히 사용자가 창을 닫아 발생한 WebView2 예외(ObjectDisposedException 등)인지 검사합니다.
                is_minor_close_err = False
                if raw_log:
                    lower_log = raw_log.lower()
                    # 닫기 동작 시 다국어로 발생 가능한 WebView2 객체 소멸 관련 키워드 정의
                    close_keywords = ['objectdisposedexception', 'webview2', '삭제된 개체', 'accessing a disposed object']
                    if any(k in lower_log for k in close_keywords):
                        # 시스템 상 중대한 설치 실패(ImportError 등)나 권한 오류가 섞여있는지 역검사
                        critical_keywords = ['importerror', 'modulenotfounderror', 'failed to install', 'permission denied']
                        if not any(ck in lower_log for ck in critical_keywords):
                            is_minor_close_err = True
                            
                    # 디스코드 보안 우회를 위한 User-Agent 설정 실패 메시지만 있는 무해한 경고의 경우도 필터링
                    if "setting user agent failed" in lower_log and len(lower_log) < 150:
                        is_minor_close_err = True

                if error_msg or (raw_log and not is_minor_close_err):
                    # 치명적이거나 식별되지 않은 프로세스 오류 스택 트레이스만 로그창에 에러로 남깁니다.
                    self.write_log('error', f"[Subprocess Log]\n{error_msg or raw_log}")
                elif raw_log and is_minor_close_err:
                    # 단순 창 종료로 인한 부차적인 로그는 메인 GUI 에러 로그에 붉은색으로 찍지 않고 백그라운드 콘솔로만 보존합니다.
                    print(f"[Debug Subprocess Log]\n{raw_log}", flush=True)
                    
                self.write_log('warn', msg['log_easy_login_cancel'])
                
        except Exception as e:
            err_trace = traceback.format_exc()
            self.write_log('error', msg['log_easy_login_err'].format(e=e))
            self.write_log('error', f"[Traceback Log]\n{err_trace}")
            # 시스템에 적절한 WebView2 런타임이 없거나 초기화 예외 발생 시,
            # 다중 브라우저 폴백(보안책) 대화상자를 즉각 트리거하여 크롬, 파이어폭스, 엣지 등을 선택할 수 있게 합니다.
            self.root.after(0, lambda: self.show_browser_fallback_dialog(e))

    def set_extracted_token(self, token):
        """추출된 토큰을 복원 입력하고 마스터 비밀번호 저장을 트리거합니다."""
        msg = MESSAGES[self.current_lang]
        self.var_token.set(token)
        self.write_log('success', msg['log_easy_login_success'])
        messagebox.showinfo(msg['ok'], msg['log_easy_login_success'])
        self.on_token_focus_out()  # 토큰 세션 암호화 저장 트리거
        
        # 메모리상 토큰 즉각 소거 (암호화 저장이 끝났으므로 복구 가능)
        try:
            wipe_memory_string(token)
        except Exception:
            pass

    def click_clear_log(self):
        self.log_area.delete("1.0", tk.END)

    def write_log(self, log_type, text):
        now_time = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{now_time}] "
        self.log_area.insert(tk.END, prefix, 'verb')
        self.log_area.insert(tk.END, text + "\n", log_type)
        
        # 로그가 너무 많이 쌓여 메모리를 지나치게 점유하거나 GUI 렌더링이 느려지는 현상을 방지하기 위해,
        # 최대 1000줄까지만 로그를 보존하고 오래된 로그 메시지는 자동으로 삭제하도록 제한합니다.
        try:
            # 'end-1c' 인덱스에서 줄 번호를 파악하여 현재 총 라인 수를 구합니다.
            total_lines = int(self.log_area.index('end-1c').split('.')[0])
            max_lines = 1000
            if total_lines > max_lines:
                # 보존할 개수를 초과한 오래된 앞줄 부분을 삭제합니다.
                # (1.0 라인부터 초과분+1.0 라인 직전까지 일괄 제거)
                delete_count = total_lines - max_lines
                self.log_area.delete("1.0", f"{delete_count + 1}.0")
        except Exception as e:
            # 자동 로그 정리 중 혹여 예외가 발생하더라도 작업이 정상 진행되도록 예외 처리합니다.
            print(f"[Warn] 로그 정리 실패: {e}")
            
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
            'pattern': None,
            'hasLink': self.var_has_link.get(),
            'hasFile': self.var_has_file.get(),
            'includeNsfw': True,
            'includePinned': self.var_include_pinned.get(),
            'backupDeleted': self.var_backup_deleted.get(),
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

    def show_browser_fallback_dialog(self, error):
        """
        WebView2 간편 로그인 창이 실패할 경우, 시스템에 설치된 실제 브라우저들(Chrome, Edge, Firefox)을 
        감지하고 사용자가 선택하여 로그인 페이지를 열 수 있는 폴백(Fallback) 다이얼로그를 제공합니다.
        """
        # 다국어 처리 텍스트 정의
        texts = {
            'ko': {
                'title': '로그인 브라우저 선택',
                'desc_title': '간편 로그인 뷰어 실행에 실패했습니다.',
                'desc_body': (
                    'Windows에 WebView2 런타임(Edge Chromium 기반)이 설치되어 있지 않거나\n'
                    '시스템 환경 상의 문제로 자동 뷰어 실행에 실패했습니다.\n\n'
                    '대신 아래에 설치된 브라우저 중 하나를 선택해 로그인 페이지를 열 수 있습니다.\n'
                    '로그인 후, 프로그램 안내에 따라 수동으로 인증 토큰을 복사하여 입력해 주세요.'
                ),
                'chrome_btn': 'Google Chrome으로 로그인',
                'edge_btn': 'Microsoft Edge로 로그인',
                'firefox_btn': 'Mozilla Firefox로 로그인',
                'default_btn': '시스템 기본 브라우저로 로그인',
                'btn_close': '닫기',
                'not_installed': ' (미설치)'
            },
            'en': {
                'title': 'Select Login Browser',
                'desc_title': 'Failed to launch the easy login window.',
                'desc_body': (
                    'Microsoft WebView2 Runtime is not installed on this system\n'
                    'or it failed to initialize due to environment limitations.\n\n'
                    'Instead, you can choose one of your installed browsers to open the login page.\n'
                    'After logging in, please follow the manual guide to copy/paste the authorization token.'
                ),
                'chrome_btn': 'Login with Google Chrome',
                'edge_btn': 'Login with Microsoft Edge',
                'firefox_btn': 'Login with Mozilla Firefox',
                'default_btn': 'Login with Default Browser',
                'btn_close': 'Close',
                'not_installed': ' (Not Installed)'
            }
        }
        
        lang = self.current_lang if self.current_lang in ['ko', 'en'] else 'ko'
        t = texts[lang]
        
        # 다이얼로그 윈도우 생성 (Tkinter Toplevel)
        dialog = tk.Toplevel(self.root)
        dialog.title(t['title'])
        dialog.geometry("520x430")
        dialog.resizable(False, False)
        dialog.configure(bg=self.bg_dark)
        
        # 모달 윈도우 지정 및 부모 창과 상호작용 설정
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 화면 중앙 배치 좌표 연산
        dialog.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()
        
        x = parent_x + (parent_w - 520) // 2
        y = parent_y + (parent_h - 430) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 상단 에러 상세 안내 레이블 영역 (디스코드 카드 형태 컨셉)
        top_frame = tk.Frame(dialog, bg=self.bg_panel, bd=0, relief='flat')
        top_frame.pack(fill='x', padx=15, pady=(15, 10))
        
        lbl_err_title = tk.Label(
            top_frame, 
            text=t['desc_title'], 
            font=('Pretendard', 11, 'bold'),
            fg=self.color_danger, 
            bg=self.bg_panel,
            anchor='w'
        )
        lbl_err_title.pack(fill='x', padx=15, pady=(12, 4))
        
        lbl_err_desc = tk.Label(
            top_frame, 
            text=t['desc_body'], 
            font=('Pretendard', 9),
            fg=self.fg_gray, 
            bg=self.bg_panel,
            justify='left',
            anchor='w'
        )
        lbl_err_desc.pack(fill='x', padx=15, pady=(0, 12))
        
        # 시스템 브라우저 탐색 모듈 비동기 로딩
        from undiscord_browser import get_available_browsers, launch_browser
        available_browsers = get_available_browsers()
        
        # 버튼 영역 컨테이너
        body_frame = tk.Frame(dialog, bg=self.bg_dark)
        body_frame.pack(fill='both', expand=True, padx=15, pady=5)
        
        def handle_browser_click(browser_key):
            # 브라우저 기동 후 다이얼로그 정리
            launch_browser(browser_key)
            dialog.destroy()
            # 로그인 창이 뜸과 동시에 토큰 수동 획득 도움말(show_help_window)을 연계 호출하여 최적의 흐름 제공
            self.show_help_window()
            
        # 1. Google Chrome 버튼 구성
        chrome_installed = 'chrome' in available_browsers
        chrome_text = t['chrome_btn'] if chrome_installed else t['chrome_btn'] + t['not_installed']
        btn_chrome = tk.Button(
            body_frame,
            text=chrome_text,
            font=('Pretendard', 9, 'bold' if chrome_installed else 'normal'),
            fg=self.fg_white if chrome_installed else "#666666",
            bg=self.color_accent if chrome_installed else "#2f3136",
            activebackground=self.bg_input,
            activeforeground=self.fg_white,
            disabledforeground="#666666",
            state='normal' if chrome_installed else 'disabled',
            bd=0,
            cursor='hand2' if chrome_installed else 'arrow',
            height=2,
            command=lambda: handle_browser_click('chrome')
        )
        btn_chrome.pack(fill='x', pady=4)
        
        # 2. Microsoft Edge 버튼 구성
        edge_installed = 'msedge' in available_browsers
        edge_text = t['edge_btn'] if edge_installed else t['edge_btn'] + t['not_installed']
        btn_edge = tk.Button(
            body_frame,
            text=edge_text,
            font=('Pretendard', 9, 'bold' if edge_installed else 'normal'),
            fg=self.fg_white if edge_installed else "#666666",
            bg=self.color_accent if edge_installed else "#2f3136",
            activebackground=self.bg_input,
            activeforeground=self.fg_white,
            disabledforeground="#666666",
            state='normal' if edge_installed else 'disabled',
            bd=0,
            cursor='hand2' if edge_installed else 'arrow',
            height=2,
            command=lambda: handle_browser_click('msedge')
        )
        btn_edge.pack(fill='x', pady=4)
        
        # 3. Mozilla Firefox 버튼 구성
        firefox_installed = 'firefox' in available_browsers
        firefox_text = t['firefox_btn'] if firefox_installed else t['firefox_btn'] + t['not_installed']
        btn_firefox = tk.Button(
            body_frame,
            text=firefox_text,
            font=('Pretendard', 9, 'bold' if firefox_installed else 'normal'),
            fg=self.fg_white if firefox_installed else "#666666",
            bg=self.color_accent if firefox_installed else "#2f3136",
            activebackground=self.bg_input,
            activeforeground=self.fg_white,
            disabledforeground="#666666",
            state='normal' if firefox_installed else 'disabled',
            bd=0,
            cursor='hand2' if firefox_installed else 'arrow',
            height=2,
            command=lambda: handle_browser_click('firefox')
        )
        btn_firefox.pack(fill='x', pady=4)
        
        # 4. 기본 웹 브라우저 폴백 버튼 구성 (기본 엣지/웨일/사파리 등 OS 설정 브라우저 기동)
        btn_default = tk.Button(
            body_frame,
            text=t['default_btn'],
            font=('Pretendard', 9),
            fg=self.fg_white,
            bg="#4f545c",
            activebackground="#686d73",
            activeforeground=self.fg_white,
            bd=0,
            cursor='hand2',
            height=2,
            command=lambda: handle_browser_click('default')
        )
        btn_default.pack(fill='x', pady=4)

        # 닫기 단추가 위치할 하단 바
        bottom_frame = tk.Frame(dialog, bg=self.bg_dark)
        bottom_frame.pack(fill='x', side='bottom', padx=15, pady=15)
        
        btn_close = tk.Button(
            bottom_frame,
            text=t['btn_close'],
            font=('Pretendard', 9),
            fg=self.fg_white,
            bg="#2f3136",
            activebackground=self.bg_input,
            activeforeground=self.fg_white,
            bd=0,
            cursor='hand2',
            width=10,
            height=1,
            command=dialog.destroy
        )
        btn_close.pack(side='right')

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
        from undiscord_login import run_login_window
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

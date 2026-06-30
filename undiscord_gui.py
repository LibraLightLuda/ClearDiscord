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
from undiscord_core import UndiscordCore
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

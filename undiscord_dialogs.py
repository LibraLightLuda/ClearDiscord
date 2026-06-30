# -*- coding: utf-8 -*-
"""
Undiscord 모달 대화창 모듈
비밀번호 생성 및 입력을 수행하는 사용자용 다이얼로그 클래스를 정의합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from undiscord_system import is_capslock_on, is_hangul_mode
from undiscord_i18n import MESSAGES

class PasswordDialog:
    """
    사용자의 중요 토큰을 암호화하거나 안전하게 복구하기 위해
    비밀번호 입력을 유도하는 모달(Modal) 윈도우 다이얼로그입니다.
    Caps Lock 및 한영키 활성 상태를 탐지하여 다국어로 경고해 줍니다.
    """
    def __init__(self, parent, mode="enter", lang="ko"):
        self.dialog = tk.Toplevel(parent)
        self.dialog.configure(bg="#2f3136")
        self.dialog.resizable(False, False)
        self.result = None
        self.mode = mode
        self.lang = lang
        
        msg = MESSAGES[lang]
        
        # 다크 테마 일관되게 적용 및 위치 보정
        main_x = parent.winfo_x()
        main_y = parent.winfo_y()
        
        if mode == "set":
            self.dialog.title(msg['dlg_set_title'])
            self.dialog.geometry(f"380x265+{main_x + 300}+{main_y + 200}")
            label_text = msg['dlg_set_desc']
        else:
            self.dialog.title(msg['dlg_enter_title'])
            self.dialog.geometry(f"380x215+{main_x + 300}+{main_y + 200}")
            label_text = msg['dlg_enter_desc']
            
        self.dialog.grab_set()  # 모달(포커스 강제) 형식 지정
        self.dialog.attributes("-topmost", True)  # 확실하게 맨 앞에 고정
        self.dialog.focus_force()  # 강제 포커싱 적용
        
        tk.Label(self.dialog, text=label_text, font=("Malgun Gothic", 9, "bold"), fg="#ffffff", bg="#2f3136", wraplength=320).pack(pady=(15, 8))
        
        # 첫 번째 비밀번호 입력창
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self.dialog, textvariable=self.entry_var, bg="#36393f", fg="#ffffff", insertbackground="#ffffff", show="*", bd=1, relief="flat", font=("Segoe UI", 10))
        self.entry.pack(fill="x", padx=30, pady=3, ipady=3)
        self.entry.focus_set()
        
        # 설정 모드일 때 재입력 확인창 추가
        self.entry_confirm_var = None
        self.entry_confirm = None
        if mode == "set":
            confirm_label = "비밀번호 재확인 입력" if lang == "ko" else "Confirm Password"
            tk.Label(self.dialog, text=confirm_label, font=("Malgun Gothic", 8, "bold"), fg="#b9bbbe", bg="#2f3136").pack(anchor="w", padx=30, pady=(4, 2))
            self.entry_confirm_var = tk.StringVar()
            self.entry_confirm = tk.Entry(self.dialog, textvariable=self.entry_confirm_var, bg="#36393f", fg="#ffffff", insertbackground="#ffffff", show="*", bd=1, relief="flat", font=("Segoe UI", 10))
            self.entry_confirm.pack(fill="x", padx=30, pady=3, ipady=3)
        
        # Caps Lock 경고 라벨 생성 (초기에는 숨김)
        self.lbl_capslock = tk.Label(self.dialog, text=msg['dlg_warn_caps'], fg="#ed4245", bg="#2f3136", font=("Malgun Gothic", 8, "bold"))
        # 한글(한영키) 경고 라벨 생성 (초기에는 숨김)
        self.lbl_hangul = tk.Label(self.dialog, text=msg['dlg_warn_ko'], fg="#e67e22", bg="#2f3136", font=("Malgun Gothic", 8, "bold"))
        
        # 버튼 영역
        btn_frame = tk.Frame(self.dialog, bg="#2f3136")
        btn_frame.pack(pady=10)
        
        self.btn_ok = ttk.Button(btn_frame, text=msg['ok'], command=self.on_ok, style="Success.TButton")
        self.btn_ok.pack(side="left", padx=5)
        
        self.btn_cancel = ttk.Button(btn_frame, text=msg['cancel'], command=self.on_cancel, style="Normal.TButton")
        self.btn_cancel.pack(side="left", padx=5)
        
        # 이벤트 바인딩 (키보드 실시간 캡스락 체크 포함)
        self.dialog.bind("<KeyPress>", self.check_capslock)
        self.dialog.bind("<Return>", lambda e: self.on_ok())
        self.dialog.bind("<Escape>", lambda e: self.on_cancel())
        
        # 기동 시 최초 상태 체크 실행
        self.check_capslock()
        
        parent.wait_window(self.dialog)
 
    def check_capslock(self, event=None):
        """Caps Lock 키 및 한영키(IME) 상태를 실시간 확인하여 사용자에게 경고 및 안내 메시지를 표시합니다."""
        # 0.05초 후에 실제 체크를 수행하여 IME 상태 업데이트 타이밍 보정
        self.dialog.after(50, self._perform_status_check)
 
    def _perform_status_check(self):
        """Caps Lock 및 한글 입력 상태의 활성화 상태에 따라 UI 라벨을 패킹하거나 제거합니다."""
        # Caps Lock 상태 체크
        if is_capslock_on():
            self.lbl_capslock.pack(after=self.entry_confirm if self.entry_confirm else self.entry, pady=(2, 0))
        else:
            self.lbl_capslock.pack_forget()
 
        # 한글(한영키) 상태 체크
        if is_hangul_mode():
            # Caps Lock 경고 라벨 뒤에 배치하거나, 없으면 바로 확인용 입력창 뒤에 배치
            anchor_lbl = self.lbl_capslock if is_capslock_on() else (self.entry_confirm if self.entry_confirm else self.entry)
            self.lbl_hangul.pack(after=anchor_lbl, pady=(2, 0))
        else:
            self.lbl_hangul.pack_forget()
 
    def on_ok(self):
        """비밀번호 검증 및 일치성 검사를 실행하고, 완료 시 입력받은 값을 캐싱 후 창을 닫습니다."""
        val = self.entry_var.get().strip()
        msg = MESSAGES[self.lang]
        
        if not val:
            warn_title = "입력 경고" if self.lang == "ko" else "Input Warning"
            warn_msg = "비밀번호를 기입해 주셔야 합니다!" if self.lang == "ko" else "You must enter a password!"
            messagebox.showwarning(warn_title, warn_msg)
            return
            
        if self.mode == "set":
            confirm_val = self.entry_confirm_var.get().strip()
            if val != confirm_val:
                mismatch_title = "비밀번호 불일치" if self.lang == "ko" else "Password Mismatch"
                mismatch_msg = (
                    "입력한 두 비밀번호가 서로 일치하지 않습니다!\n정확하게 다시 입력해 주세요."
                    if self.lang == "ko" else
                    "The passwords do not match!\nPlease type carefully and try again."
                )
                messagebox.showerror(mismatch_title, mismatch_msg)
                return
                
        self.result = val
        self.dialog.destroy()
 
    def on_cancel(self):
        """사용자가 입력을 취소한 경우 별도의 캐싱 없이 즉각 다이얼로그를 파괴합니다."""
        self.dialog.destroy()

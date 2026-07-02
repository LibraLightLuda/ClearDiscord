# -*- coding: utf-8 -*-
"""
Undiscord 마스터 패스워드 및 인증 토큰 암/복호화 라이프사이클 관리 모듈
"""

from tkinter import messagebox
from undiscord_i18n import MESSAGES
from undiscord_crypto import decrypt_data, wipe_memory_string
from undiscord_dialogs import PasswordDialog

def restore_token_session(app, data):
    """config.json의 암호화된 토큰 데이터를 마스터 비밀번호 입력을 통해 안전하게 복호화하고 UI 세션에 로드합니다."""
    msg = MESSAGES[app.current_lang]
    
    # 1단계: 암호화 안 된 평문 토큰 복구 시도 (하위 호환)
    if 'token' in data and data['token']:
        app.var_token.set(data['token'])
        app.session_password = ""
        return
        
    # 2단계: 암호화된 토큰 파라미터가 있을 때의 암호 팝업 복구 루프
    enc_token = data.get('encryptedToken', '')
    salt_val = data.get('salt', '')
    verify_val = data.get('verification', '')
    
    if enc_token and salt_val and verify_val:
        retry_count = 0
        while retry_count < 3:
            dlg = PasswordDialog(
                app.root, 
                title=msg['pass_title'], 
                prompt=msg['pass_prompt'] if retry_count == 0 else msg['pass_retry_prompt'],
                is_create=False,
                lang=app.current_lang
            )
            app.root.wait_window(dlg)
            
            if dlg.result is not None:
                # 사용자가 비밀번호를 입력한 경우
                input_pass = dlg.result
                try:
                    dec_token = decrypt_data(enc_token, input_pass, salt_val, verify_val)
                    app.var_token.set(dec_token)
                    app.session_password = input_pass
                    
                    # 메모리 보호: 사용 완료된 평문 문자열은 즉시 소거
                    wipe_memory_string(dec_token)
                    app.write_log('success', msg['pass_decrypt_success'])
                    return
                except ValueError:
                    # 복호화 실패 시 재시도 안내
                    retry_count += 1
                    messagebox.showerror(msg['pass_err_title'], msg['pass_decrypt_fail'])
            else:
                # 사용자가 입력을 취소(Cancel)한 경우
                app.write_log('warn', msg['pass_decrypt_cancel_warn'])
                app.session_password = ""
                break
                
        if retry_count >= 3:
            # 3회 초과 오류 시 안전 격리 경고
            app.write_log('error', msg['pass_decrypt_lockout'])
            messagebox.showerror(msg['pass_err_title'], msg['pass_decrypt_lockout'])
            app.session_password = ""

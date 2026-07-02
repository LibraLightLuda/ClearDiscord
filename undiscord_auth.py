# -*- coding: utf-8 -*-
"""
Undiscord 마스터 패스워드 및 인증 토큰 암/복호화 라이프사이클 관리 모듈
"""

import json
from tkinter import messagebox
from undiscord_i18n import MESSAGES
from undiscord_crypto import decrypt_data, wipe_memory_string
from undiscord_dialogs import PasswordDialog
from undiscord_layout import update_ui_texts

def restore_token_session(app, data):
    """config.json의 암호화된 토큰 데이터를 마스터 비밀번호 입력을 통해 안전하게 복호화하고 UI 세션에 로드합니다."""
    msg = MESSAGES[app.current_lang]
    
    # 1단계: 암호화 안 된 평문 토큰 복구 시도 (하위 호환)
    if 'token' in data and data['token']:
        app.var_token.set(data['token'])
        app.session_password = ""
        app.write_log('success', "저장된 평문 토큰을 성공적으로 로드했습니다." if app.current_lang == 'ko' else "Successfully loaded the stored plaintext token.")
        update_ui_texts(app)
        app.root.deiconify()
        return
        
    # 2단계: 암호화된 토큰 파라미터가 있을 때의 암호 팝업 복구 루프
    enc_token = data.get('encryptedToken', '')
    salt_val = data.get('salt', '')
    verify_val = data.get('verification', '')
    
    if enc_token and salt_val and verify_val:
        app.var_token.set("")  # 검증 전까지 토큰 공란 처리
        retry_count = 0
        max_attempts = 3
        success = False
        
        while retry_count < max_attempts:
            # 복호화용 패스워드 입력창은 mode="enter"로 띄웁니다.
            dlg = PasswordDialog(
                app.root, 
                mode="enter",
                lang=app.current_lang
            )
            app.root.wait_window(dlg)
            
            if dlg.result is not None:
                if dlg.result == "":
                    # 빈 비밀번호 취소 처리
                    app.write_log('warn', msg['pass_cancel_warn'])
                    app.session_password = None
                    break
                    
                input_pass = dlg.result
                try:
                    dec_token = decrypt_data(enc_token, input_pass, salt_val, verify_val)
                    app.var_token.set(dec_token)
                    app.session_password = input_pass
                    
                    # 메모리 보호: 사용 완료된 평문 문자열은 즉시 소거
                    wipe_memory_string(dec_token)
                    app.write_log('success', msg['pass_verify_success'])
                    success = True
                    break
                except ValueError:
                    # 복호화 실패 시 재시도 안내
                    retry_count += 1
                    left = max_attempts - retry_count
                    if left > 0:
                        messagebox.showerror(msg['pass_err_title'], msg['pass_verify_fail_fmt'].format(left=left))
                    else:
                        # 3회 연속 오답 시 로컬 보안 보호를 위해 저장 데이터 파괴
                        messagebox.showerror(msg['pass_destroy_title'], msg['pass_destroy_msg'])
                        app.session_password = None
                        app.var_token.set("")
                        
                        # JSON 설정 파일 암호화 지표 초기화 기록
                        data['encryptedToken'] = ""
                        data['salt'] = ""
                        data['verification'] = ""
                        data['token'] = ""
                        try:
                            with open("config.json", "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=4, ensure_ascii=False)
                            app.write_log('error', msg['log_pass_destroy'])
                        except Exception as ex:
                            app.write_log('error', msg['log_pass_destroy_err'].format(ex=ex))
                        break
            else:
                # 사용자가 입력을 취소(Cancel)한 경우
                app.write_log('warn', msg['pass_cancel_warn'])
                app.session_password = None
                break
                
        if success:
            update_ui_texts(app)
            # 비밀번호 검증 성공 시에만 메인 창 노출
            app.root.deiconify()
        else:
            # 취소 또는 3회 실패 시 즉각 프로그램 파괴/완전 종료
            if retry_count >= max_attempts:
                messagebox.showerror(msg['err_title'], msg['pass_block_err'])
            app.root.destroy()
            return
            
    else:
        # 최초 실행 등으로 인해 비밀번호 정보가 아예 저장되지 않은 경우 실행 시 우선 설정하도록 강제
        app.write_log('info', msg['log_pass_no_exist'])
        dlg = PasswordDialog(app.root, mode="set", lang=app.current_lang)
        app.root.wait_window(dlg)
        
        if dlg.result is not None:
            if dlg.result == "":
                app.session_password = ""
                app.write_log('success', "비밀번호 설정 없이 평문으로 저장되도록 시작합니다." if app.current_lang == 'ko' else "Started without password. Tokens will be saved in plaintext.")
                app.save_config()
                app.root.deiconify()
            elif len(dlg.result) < 8:
                messagebox.showerror(msg['pass_err_title'], msg['pass_len_error_exit'].replace("종료합니다", "평문 모드로 진행합니다").replace("Aborting execution", "Proceeding in plaintext mode"))
                app.session_password = ""
                app.save_config()
                app.root.deiconify()
            else:
                app.session_password = dlg.result
                app.write_log('success', msg['log_pass_init_ok'])
                app.save_config()
                # 설정 성공했으므로 메인 창 노출
                app.root.deiconify()
        else:
            app.write_log('warn', msg['pass_cancel_exit'])
            app.root.destroy()
            return

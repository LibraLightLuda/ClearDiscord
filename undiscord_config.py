# -*- coding: utf-8 -*-
"""
Undiscord 설정 입출력 모듈
config.json 파일 저장 및 복원, 위젯 매핑 복구를 수행합니다.
"""

import os
import json
import tkinter as tk
from tkinter import messagebox
from undiscord_i18n import get_system_language, MESSAGES
from undiscord_utils import calculate_relative_date

def save_config(app):
    """현재 GUI 입력 상태와 각종 설정 필터 변수들을 config.json으로 안전하게 저장합니다."""
    msg = MESSAGES[app.current_lang]
    
    # 마스터 비밀번호 세션이 만료/없음인 경우, 토큰 원문 평문 저장 여부
    enc_token = ""
    salt_val = ""
    verify_val = ""
    token_plain = app.var_token.get()
    
    if app.session_password:
        from undiscord_crypto import encrypt_data
        try:
            enc_token, salt_val, verify_val = encrypt_data(token_plain, app.session_password)
        except Exception as e:
            app.write_log('error', msg['pass_crypt_err'].format(e=e))
            return
            
    config_data = {
        'guildId': app.var_guild_id.get(),
        'channelId': app.var_channel_id.get(),
        'authorId': app.var_author_id.get(),
        'minRange': app.var_min_range.get(),
        'maxRange': app.var_max_range.get(),
        'minQuickSelect': app.combo_min_quick.current(),
        'maxQuickSelect': app.combo_max_quick.current(),
        'searchText': app.var_search_text.get(),
        'pattern': "",
        'hasLink': app.var_has_link.get(),
        'hasFile': app.var_has_file.get(),
        'includeNsfw': True,
        'includePinned': app.var_include_pinned.get(),
        'backupDeleted': app.var_backup_deleted.get(),
        'searchDelay': app.var_search_delay.get(),
        'minDelay': app.var_min_delay.get(),
        'maxDelay': app.var_max_delay.get(),
        'language': app.current_lang,
        'encryptedToken': enc_token,
        'salt': salt_val,
        'verification': verify_val,
        'token': token_plain if not app.session_password else ""
    }
    
    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        try:
            app.write_log('warn', msg['pass_config_err'].format(e=e))
        except Exception:
            pass


def load_config(app):
    """로컬 config.json 파일로부터 위젯 값을 복구하고, 토큰 복구 흐름을 기동합니다."""
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
        app.root.destroy()
        return

    data = {}
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"설정 로드 중 오류: {e}")
            
    # 언어 설정 복원
    if 'language' in data:
        app.current_lang = data['language']
        
    from undiscord_layout import update_ui_texts
    update_ui_texts(app)
    
    msg = MESSAGES[app.current_lang]
    
    if 'guildId' in data: app.var_guild_id.set(data['guildId'])
    if 'channelId' in data: app.var_channel_id.set(data['channelId'])
    if 'authorId' in data: app.var_author_id.set(data['authorId'])
    
    # 퀵 셀렉트 콤보박스 설정 먼저 로드
    if 'minQuickSelect' in data:
        try:
            app.combo_min_quick.current(data['minQuickSelect'])
        except Exception:
            pass
    if 'maxQuickSelect' in data:
        try:
            app.combo_max_quick.current(data['maxQuickSelect'])
        except Exception:
            pass

    # 퀵 셀렉트 설정에 따라 현재 시간 기준으로 자동 갱신. "직접 입력"인 경우에는 저장된 이전 값을 복구
    min_sel = app.combo_min_quick.get()
    manual_str = msg['quick_options'][0]
    if min_sel and min_sel != manual_str:
        app.var_min_range.set(calculate_relative_date(min_sel))
    elif 'minRange' in data:
        app.var_min_range.set(data['minRange'])

    max_sel = app.combo_max_quick.get()
    if max_sel and max_sel != manual_str:
        app.var_max_range.set(calculate_relative_date(max_sel))
    elif 'maxRange' in data:
        app.var_max_range.set(data['maxRange'])

    if 'searchText' in data: app.var_search_text.set(data['searchText'])
    if 'hasLink' in data: app.var_has_link.set(data['hasLink'])
    if 'hasFile' in data: app.var_has_file.set(data['hasFile'])
    if 'includePinned' in data: app.var_include_pinned.set(data['includePinned'])
    if 'backupDeleted' in data: app.var_backup_deleted.set(data['backupDeleted'])
    
    # 설정 복원 후 체크박스 활성/비활성 UX 텍스트 업데이트
    from undiscord_layout import update_checkbox_ux
    update_checkbox_ux(app)
    
    if 'searchDelay' in data: app.var_search_delay.set(data['searchDelay'])
    if 'minDelay' in data: app.var_min_delay.set(data['minDelay'])
    if 'maxDelay' in data: app.var_max_delay.set(data['maxDelay'])
    
    # 세션 마스터 비밀번호 및 암호화 토큰 복호화 구동 흐름 위임
    from undiscord_auth import restore_token_session
    restore_token_session(app, data)

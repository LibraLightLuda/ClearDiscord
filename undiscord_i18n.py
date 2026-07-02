# -*- coding: utf-8 -*-
"""
Undiscord 다국어 지원(i18n) 모듈
시스템 로케일을 감지하여 기본 언어(ko/en)를 판단하고,
UI 텍스트 및 로그, 팝업 메시지를 한국어와 영어로 일치시키는 리소스를 통합 관리합니다.
"""

import locale
import sys

def get_system_language() -> str:
    """
    OS 환경 설정을 기반으로 기본 표시 언어를 결정합니다.
    시스템 로케일이 한국어('ko') 계열일 경우 'ko'를 반환하며, 그 외에는 모두 'en'(영어)을 반환합니다.
    """
    try:
        # Windows 환경에서 시스템 UI 표시 언어를 더 정확히 가져오기 위해 ctypes 시도
        if sys.platform == 'win32':
            import ctypes
            # GetUserDefaultUILanguage: 한국어는 1042(0x0412)
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if lang_id == 1042 or (lang_id & 0xff) == 0x12:
                return 'ko'
        
        # 일반적인 locale 체크
        default_locale, _ = locale.getdefaultlocale()
        if default_locale and default_locale.lower().startswith('ko'):
            return 'ko'
    except Exception:
        pass
    return 'en'


# ==================================================
# 다국어 메시지 리소스 매핑 (한국어 / 영어)
# ==================================================
MESSAGES = {
    'ko': {
        'title': "Undiscord Python GUI Dashboard",
        
        # 카드 프레임 제목
        'card_auth_title': "  인증 설정  ",
        'card_target_title': "  삭제 대상 위치 및 범위  ",
        'card_filter_title': "  메시지 상세 필터링  ",
        'card_delay_title': "  지연 시간 및 우회 속도 설정  ",
        
        # 카드 1: 인증 설정
        'token_label': "디스코드 인증 토큰 *",
        'btn_view': "보기",
        'btn_hide': "숨기기",
        'btn_easy_login': "간편 로그인",
        'author_id_label': "작성자 ID (미입력 시 내 계정으로 자동 기입)",
        
        # 카드 2: 위치 및 범위
        'guild_id_label': "서버 ID (DM일 경우 @me 입력) *",
        'channel_id_label': "채널 ID (쉼표[,]로 다중 채널 구분 입력 가능) *",
        'min_range_label': "삭제 시작 범위 (이 시각 이후 메시지)",
        'max_range_label': "삭제 종료 범위 (이 시각 이전 메시지)",
        'min_quick_lbl': "└ 삭제 시작시점 자동완성",
        'max_quick_lbl': "└ 삭제 종료시점 자동완성",
        
        # 콤보박스 선택지 (시작/종료)
        'quick_options': [
            "직접 입력 (사용자 설정)", "현재 시각", "1시간 전", "6시간 전", 
            "1일 전 (24h)", "3일 전", "1주일 전", "2주일 전", 
            "1달 전", "3달 전", "6달 전", "1년 전"
        ],
        
        # 카드 3: 상세 필터링
        'search_text_label': "텍스트 검색어 필터",
        'pattern_label': "정규표현식 매칭 필터",
        'chk_has_link': "링크 포함 메시지만 삭제",
        'chk_has_file': "파일 첨부 메시지만 삭제",
        'chk_include_nsfw': "NSFW 채널 검색 포함",
        'chk_include_pinned': "핀 고정 메시지도 삭제",
        
        # 카드 4: 지연 대기 설정
        'search_delay_label': "검색 대기 시간 (밀리초)",
        'min_delay_label': "최소 삭제 대기 (밀리초)",
        'max_delay_label': "최대 삭제 대기 (밀리초)",
        
        # 하단 좌측 컨트롤 패널
        'app_desc': "디스코드 메시지 일괄 삭제 도구 (파이썬 V1.0)",
        'made_by': "만든이: ",
        'open_source': "  |  오픈소스: ",
        'btn_start': "작업 시작",
        'btn_stop': "작업 중단",
        'btn_clear': "로그 창 비우기",
        'btn_help': "이용 도움말 (인증키 및 ID 획득법)",
        
        # 하단 우측 진행 상태
        'progress_wait': "대기 중 - 옵션을 입력한 뒤 [작업 시작]을 누르세요.",
        'progress_status_fmt': "진행 상황: {percent}% ({val}/{total}) | 성공: {del_count}건, 실패: {fail_count}건 | 경과 시간: {elapsed} | 남은 예상 시간: {remaining}",
        'progress_finished_fmt': "작업 종료됨 - 성공: {del_count}건, 실패: {fail_count}건",
        
        # 다이어로그 공통 및 버튼
        'ok': "확인",
        'cancel': "취소",
        'yes': "예",
        'no': "아니오",
        'pass_use_none': "사용안함",
        
        # 입력 에러 메시지
        'err_title': "입력 에러",
        'err_delay_number': "지연 대기 설정 필드에는 양의 정수(숫자)만 기입할 수 있습니다!",
        'err_token_empty': "디스코드 인증 토큰을 반드시 기입해야 합니다!",
        'err_guild_empty': "서버 ID를 기입해야 합니다.\n개인 DM 대화일 경우 @me를 입력하세요.",
        'err_channel_empty': "채널 ID를 기입해야 합니다!",
        
        # 비밀번호 설정 관련 팝업
        'pass_err_title': "비밀번호 오류",
        'pass_len_error': "비밀번호는 보안상 최소 8자 이상으로 입력해야 합니다. 암호화 설정을 스킵합니다.",
        'pass_len_error_exit': "비밀번호는 최소 8자 이상으로 입력해야 합니다. 비밀번호 설정을 건너뛰고 종료합니다.",
        'pass_cancel_warn': "비밀번호 설정을 취소하여 토큰 자동 보호 설정이 보류되었습니다.",
        'pass_cancel_exit': "마스터 비밀번호 설정이 필요하므로 프로그램 실행을 중단합니다.",
        'pass_verify_success': "비밀번호 검증이 완료되어 디스코드 인증 토큰을 복원했습니다.",
        'pass_verify_fail_fmt': "비밀번호가 올바르지 않습니다. (남은 입력 가능 횟수: {left}회)",
        'pass_destroy_title': "보안 영구 파기",
        'pass_destroy_msg': "비밀번호를 3회 연속 틀려 보안을 위해 저장된 토큰 정보를 즉각 삭제합니다!",
        'pass_token_skip_warn': "비밀번호 입력을 생략하여 토큰 저장을 건너뛰었습니다.",
        'pass_crypt_err': "토큰 암호화 과정 중 실패: {e}",
        'pass_config_err': "[경고] 설정을 파일에 저장하지 못했습니다: {e}",
        'pass_block_err': "올바른 마스터 비밀번호 인증 없이는 프로그램 실행이 차단됩니다.",
        'pass_plain_warn_title': "평문 저장 경고",
        'pass_plain_warn_msg': "비밀번호를 입력하지 않으면 토큰이 암호화되지 않은 채 평문으로 저장되어 보안에 취약할 수 있습니다.\n정말 비밀번호 없이 진행하시겠습니까?",
        'status_encrypted': "보안 수준: 암호화 활성화됨 (AES-256-GCM)",
        'status_plaintext': "보안 수준: 암호화 미사용 (평문 저장됨 - 위험)",
        
        # 마스터 비밀번호 모달 다이어로그 내부 라벨
        'dlg_set_title': "마스터 비밀번호 신규 설정",
        'dlg_enter_title': "마스터 비밀번호 입력",
        'dlg_set_desc': "토큰 보호용 마스터 비밀번호를 새로 설정하십시오. (최소 8자)",
        'dlg_enter_desc': "보관된 디스코드 토큰을 안전하게 해독하기 위해 비밀번호를 입력하십시오.",
        'dlg_pass_label': "비밀번호 입력",
        'dlg_warn_caps': "※ 경고: 현재 Caps Lock이 켜져 있습니다.",
        'dlg_warn_ko': "※ 경고: 현재 한/영 키가 활성화되어 있어 한글이 입력될 수 있습니다.",
        
        # 자동 선택 관련 다국어
        'btn_load_guilds': "서버 불러오기",
        'combo_guild_placeholder': "--- 서버 자동 선택 (클릭) ---",
        'combo_channel_placeholder': "--- 채널 자동 선택 (클릭) ---",
        'dm_display_name': "👤 개인 DM 및 그룹 DM (@me)",
        'log_fetch_guilds_start': "디스코드 서버 목록을 불러오는 중...",
        'log_fetch_guilds_success': "서버 목록 {count}개를 성공적으로 가져왔습니다.",
        'log_fetch_channels_success': "채널 목록 {count}개를 성공적으로 가져왔습니다.",
        'err_token_required_for_fetch': "서버 목록 조회를 위해 디스코드 토큰 입력이 먼저 필요합니다!",
        'err_fetch_failed': "목록 로드 실패: {e}",
        
        # 로그 출력 메시지
        'log_easy_login_start': "디스코드 간편 로그인 창을 실행합니다. 브라우저에서 로그인을 완료하면 토큰이 자동으로 입력됩니다.",
        'log_easy_login_success': "성공적으로 로그인 토큰을 가져왔습니다!",
        'log_easy_login_cancel': "디스코드 간편 로그인이 완료되지 않았거나 취소되었습니다.",
        'log_easy_login_err': "간편 로그인 실행 실패: {e}",
        'err_easy_login_install': "간편 로그인 기능을 실행하려면 'pywebview' 라이브러리가 필요합니다. 자동 설치 중...",
        'log_search_author': "작성자 ID가 입력되지 않아 디스코드 인증 토큰의 본인 고유 계정 ID를 조회합니다...",
        'log_author_auto_set': "본인 계정 ID를 자동으로 불러와 적용했습니다: {my_id}",
        'log_author_fail': "본인 계정 ID 자동 조회 실패 (응답 코드: {status}). 전체 메시지 기준으로 검색 및 삭제가 수행될 수 있습니다.",
        'log_author_net_err': "본인 계정 ID 네트워크 조회 중 오류 발생: {e}",
        'log_stop_cmd': "정지 명령 전송 완료. 현재 삭제 진행 중인 작업까지만 수행하고 중단됩니다...",
        'log_pass_destroy': "비밀번호 입력 3회 오류로 로컬 토큰 파일을 영구 삭제하였습니다.",
        'log_pass_destroy_err': "토큰 파기 중 에러 발생: {ex}",
        'log_pass_no_exist': "[안내] 마스터 비밀번호가 설정되어 있지 않아 안전한 저장 보호를 위해 비밀번호 설정을 수행합니다.",
        'log_pass_init_ok': "마스터 비밀번호 설정이 완료되었습니다. 토큰 입력 시 이 비밀번호로 자동 암호화 보존됩니다.",
        
        # 확인 팝업창
        'confirm_exit_title': "종료 확인",
        'confirm_exit_msg': "현재 메시지 삭제 작업이 실행 중입니다.\n강제 중단하고 프로그램을 종료하시겠습니까?",
        'confirm_start_title': "삭제 확인",
        
        # 도움말 창
        'help_title': "💡 디스코드 고유 정보 발급 및 찾기 가이드",
        'help_tab1': " 인증 토큰 복사 방법 ",
        'help_tab2': " 서버 및 채널 아이디(ID) 복사 방법 ",
        'help_tab3': " 날짜 범위 및 필터 활용법 ",
        
        'help_text_token': (
            "■ 디스코드 인증 토큰(Authorization Token) 발급 방법\n\n"
            "인증 토큰은 사용자의 디스코드 계정 고유 인증 키입니다.\n"
            "⚠️ 중요: 이 토큰을 타인에게 알려주면 계정을 탈취당할 수 있으니 절대 공유하지 마세요!\n\n"
            "--------------------------------------------------------------------------------\n\n"
            "1. PC에서 크롬(Chrome) 또는 엣지(Edge) 브라우저를 열고 디스코드 웹사이트(discord.com/app)에 로그인합니다.\n\n"
            "2. 키보드 맨 위의 [F12] 키를 누르거나, 화면 빈 곳 우클릭 후 [검사]를 눌러 개발자 도구를 켭니다.\n\n"
            "3. 개발자 도구 창의 상단 메뉴 탭 중에서 [네트워크 (Network)] 탭을 찾아 클릭합니다.\n\n"
            "4. 좌측 상단 깔때기 모양 옆의 입력칸(Filter)에 '/messages' 라고 입력합니다.\n\n"
            "5. 그 상태에서 디스코드 웹페이지의 아무 채팅 채널을 클릭하거나 대화방에 메시지를 하나 전송합니다.\n\n"
            "6. 개발자 도구의 네트워크 목록에 새로 뜨는 요청 항목(예: messages)을 클릭합니다.\n\n"
            "7. 우측에 나타나는 상세 영역에서 [헤더 (Headers)] 탭을 클릭합니다.\n\n"
            "8. 아래로 스크롤하여 [요청 헤더 (Request Headers)] 그룹을 찾습니다.\n\n"
            "9. 목록 항목 중 'Authorization' 이라는 단어를 찾아, 그 오른쪽에 적힌 길고 복잡한 영어/숫자 값 전체를 복사합니다.\n\n"
            "10. 복사한 값을 프로그램 상단의 '디스코드 인증 토큰' 입력란에 붙여넣으시면 됩니다."
        ),
        'help_text_ids': (
            "■ 디스코드 서버 ID 및 채널 ID 획득 방법\n\n"
            "디스코드의 고유 식별값(ID)을 복사하려면 먼저 디스코드 프로그램에서 '개발자 모드'를 활성화해야 합니다.\n\n"
            "--------------------------------------------------------------------------------\n\n"
            "1. 디스코드 프로그램 왼쪽 아래에 있는 톱니바퀴 아이콘 [사용자 설정]을 클릭합니다.\n\n"
            "2. 왼쪽 메뉴들을 아래로 스크롤하여 앱 설정 항목 아래의 [고급] 메뉴를 클릭합니다.\n\n"
            "3. 맨 위에 표시되는 [개발자 모드] 스위치를 켜서 활성화해 줍니다.\n\n"
            "4. 설정창을 닫고 다시 메인 화면으로 돌아옵니다.\n\n"
            "5. [서버 ID 복사]:\n"
            "   - 왼쪽의 서버 목록에서 원하는 서버의 동그란 아이콘에 마우스 우클릭을 합니다.\n"
            "   - 맨 아래에 표시되는 [ID 복사하기]를 클릭하여 프로그램의 '서버 ID' 칸에 붙여넣습니다.\n"
            "   ※ 개인 DM방 메시지를 지우는 경우 서버 ID 칸에 '@me' 라고 입력해 주세요.\n\n"
            "6. [채널 ID 복사]:\n"
            "   - 메시지를 지우고 싶은 텍스트 채널 이름에 마우스 우클릭을 합니다.\n"
            "   - 맨 아래에 뜨는 [ID 복사하기]를 눌러 프로그램의 '채널 ID' 칸에 붙여넣습니다.\n"
            "   - 쉼표(,)를 기입하면 한 번에 여러 개의 채널을 연속으로 작업시킬 수도 있습니다."
        ),
        'help_text_filters': (
            "■ 날짜 범위 퀵 셀렉트 및 고성능 필터 기능 설명\n\n"
            "본 프로그램은 원치 않는 메시지만 정확하게 골라 삭제할 수 있는 특화 필터를 지원합니다.\n\n"
            "--------------------------------------------------------------------------------\n\n"
            "1. [삭제 범위 지정 및 퀵 셀렉트 자동완성]\n"
            "   - '삭제 시작 범위'와 '종료 범위'는 직접 디스코드 Snowflake ID를 기입하거나,\n"
            "     하단의 드롭다운 메뉴(예: '1일 전', '1주일 전' 등)를 통해 기동 시점을 기준으로 자동 계산해 채울 수 있습니다.\n"
            "   - 시작 범위 이후부터 종료 범위 이전의 메시지들만 안전하게 타겟팅됩니다.\n\n"
            "2. [텍스트 및 정규표현식(Regex) 매칭 필터]\n"
            "   - 텍스트 검색어 필터: 특정 단어가 포함된 메시지만 골라 지웁니다.\n"
            "   - 정규표현식 매칭 필터: 조금 더 고차원적인 패턴 매칭(예: 전화번호, 이메일, 특정 양식)을 정밀 필터링합니다.\n\n"
            "3. [파일 및 링크 첨부 메시지 전용 필터]\n"
            "   - '링크 포함 메시지만 삭제': 일반 대화는 남기고 외부 URL 링크가 적힌 메시지만 삭제합니다.\n"
            "   - '파일 첨부 메시지만 삭제': 이미지, zip 등 파일이 업로드된 메시지만 삭제하여 채널 용량을 확보합니다.\n\n"
            "4. [보안 고정 메시지 옵션]\n"
            "   - 기본적으로 디스코드 방에 핀 고정(Pinned)된 메시지는 안전을 위해 삭제 대상에서 자동 제외됩니다.\n"
            "   - 만약 핀 고정 메시지도 전부 지우기를 원하시면 '핀 고정 메시지도 삭제' 체크박스를 체크하십시오.\n\n"
            "5. [지연 시간 대기 설정]\n"
            "   - 검색 및 삭제 간격은 밀리초(ms) 단위로 조절 가능합니다.\n"
            "   - 디스코드의 API Rate Limit 차단을 우회하기 위해 '최소 1500ms ~ 최대 3000ms'의 랜덤 딜레이 적용을 적극 권장합니다."
        ),
        
        # 엔진 로그 다국어 번역
        'log_engine_delay': "-> 랜덤 우회 지연 대기: {val:.2f}초",
        'log_engine_search_http_err': "검색 HTTP 요청 예외: {e}",
        'log_engine_indexing': "디스코드 서버가 검색 데이터를 인덱싱 중입니다. {retry_after}초 후 다시 시도합니다...",
        'log_engine_rate_limit_search': "검색 API 한도 도달! {wait_time}초 대기 후 검색 지연을 늘려 재시도합니다...",
        'log_engine_search_fail': "메시지 검색 실패! API 응답 코드: {status}, 본문: {err}",
        'log_engine_regex_fail': "정규표현식 패턴 필터링 실패: {e}",
        'log_engine_delete_http_err': "메시지 삭제 요청 에러: {e}",
        'log_engine_rate_limit_delete': "삭제 API 한도 도달! {retry_after}초 대기 후 최소/최대 지연 범위를 {w}밀리초 ~ {w+1500}밀리초로 강제 상향 조절합니다...",
        'log_engine_archive_thread': "스레드가 아카이브 상태라 지울 수 없습니다. 오프셋을 증가시켜 통과합니다.",
        'log_engine_delete_fail': "삭제 에러! API 상태 코드: {status}, 상세: {text}",
        'log_engine_stop_user': "사용자에 의해 삭제 작업이 중지되었습니다.",
        'log_engine_info_fmt': "[{del_count}/{total}] 작성일: {time} | 작성자: {username} | 내용: {content} (ID: {id})",
        'log_engine_retry': "삭제 재시도 대기: {delay}초... ({attempt}/{max_attempt})",
        'log_engine_consecutive_fails': "삭제 실패가 연속으로 5회 도달했습니다. 토큰이나 인터넷 망을 점검해 주세요. 안전을 위해 작업을 강제 자동 중단합니다.",
        'log_engine_running': "이미 엔진이 작동 중입니다.",
        'log_engine_started': "삭제 작업을 시작했습니다. (시작 시각: {time})",
        'log_engine_params': "설정 파라미터 - 작성자 ID: {author_id}, 서버 ID: {guild_id}, 채널 ID: {channel_id}",
        'log_engine_fetching': "API를 통해 메시지를 가져오는 중...",
        'log_engine_loop_err': "작업 루프 비정상 종료 (에러: {e})",
        'log_engine_summary': "누적 전체 대상: {total}건 | 현재 페이지 수집: {found}건 | 삭제 대상: {to_delete}건 | 제외 대상: {skipped}건 | 현재 오프셋: {offset}",
        'log_engine_stats_delay': "대기 설정 - 랜덤 삭제 대기 범위: {min_d}밀리초 ~ {max_d}밀리초, 검색 대기: {search}밀리초",
        'log_engine_stats_ping': "응답 핑(Ping): {ping}밀리초, 평균 핑: {avg_ping}밀리초",
        'log_engine_stats_throttled': "호출 차단 횟수: {count}회, 누적 대기 시간: {time}",
        'log_engine_etr': "예상 남은 시간: {etr}",
        'log_engine_confirm_msg': "검색 결과 약 {total}개의 메시지가 감지되었습니다.\n삭제를 승인하고 진행하시겠습니까? (예상 대기 시간: {etr})\n\n---- 본문 미리보기 (최대 5건) ----\n{preview}",
        'log_engine_confirm_cancel': "사용자가 확인창에서 삭제를 취소했습니다.",
        'log_engine_skip_page': "현재 페이지에 삭제할 메시지가 존재하지 않습니다. 검색 범위를 조절하여 다음 페이지로 넘어갑니다. (오프셋: {old} -> {new})",
        'log_engine_api_end': "검색 결과의 끝에 도달했습니다. (API 빈 페이지 반환)",
        'log_engine_empty_retry': "검색 결과가 없습니다. 재검색을 시도합니다. ({attempt}/{max_attempt})",
        'log_engine_next_page': "다음 검색 페이지 요청 대기: {delay}초...",
        'log_engine_finished': "삭제 프로세스가 완전히 종료되었습니다. (종료 시각: {time})",
        'log_engine_time_summary': "총 수행 시간: {time} | 삭제 성공: {del_count}건 | 삭제 실패: {fail_count}건",
        'log_engine_batch_setup': "총 {count}개 채널에 대한 배치 삭제를 구성합니다.",
        'log_engine_batch_start': ">>> 배치 작업 시작 ({idx}/{total}) - 채널 ID: {channel_id}",
        'log_engine_batch_finished': "모든 배치 채널 작업이 종결되었습니다."
    },
    
    # ----------------------------------------------------
    # English Translations
    # ----------------------------------------------------
    'en': {
        'title': "Undiscord Python GUI Dashboard",
        
        # Card Frame Titles
        'card_auth_title': "  Authentication Settings  ",
        'card_target_title': "  Target Location & Date Range  ",
        'card_filter_title': "  Detailed Message Filtering  ",
        'card_delay_title': "  Delay Time & Rate-Limit Bypass  ",
        
        # Card 1: Auth Settings
        'token_label': "Discord Auth Token *",
        'btn_view': "Show",
        'btn_hide': "Hide",
        'btn_easy_login': "Easy Login",
        'author_id_label': "Author ID (Leave blank to auto-fetch your ID)",
        
        # Card 2: Target & Range
        'guild_id_label': "Server ID (Enter @me for DMs) *",
        'channel_id_label': "Channel ID (Comma [,] separated for multiple channels) *",
        'min_range_label': "Start Date Range (Messages after this date)",
        'max_range_label': "End Date Range (Messages before this date)",
        'min_quick_lbl': "└ Auto-fill Start Range",
        'max_quick_lbl': "└ Auto-fill End Range",
        
        # Combobox Options (Start/End)
        'quick_options': [
            "Manual Input (User Custom)", "Current Time", "1 hour ago", "6 hours ago", 
            "1 day ago (24h)", "3 days ago", "1 week ago", "2 weeks ago", 
            "1 month ago", "3 months ago", "6 months ago", "1 year ago"
        ],
        
        # Card 3: Filters
        'search_text_label': "Text Query Search Filter",
        'pattern_label': "Regular Expression (Regex) Filter",
        'chk_has_link': "Only delete messages containing Links",
        'chk_has_file': "Only delete messages containing Files",
        'chk_include_nsfw': "Include NSFW Channels in search",
        'chk_include_pinned': "Also delete Pinned messages",
        
        # Card 4: Delay Settings
        'search_delay_label': "Search Wait Time (milliseconds)",
        'min_delay_label': "Min Delete Delay (milliseconds)",
        'max_delay_label': "Max Delete Delay (milliseconds)",
        
        # Bottom Left Ctrl Panel
        'app_desc': "Discord Message Bulk Deletion Utility (Python V1.0)",
        'made_by': "Author: ",
        'open_source': "  |  Open Source: ",
        'btn_start': "Start Deletion",
        'btn_stop': "Stop Job",
        'btn_clear': "Clear Logs",
        'btn_help': "User Manual (How to get Token / IDs)",
        
        # Bottom Right Progress Panel
        'progress_wait': "Idle - Fill in options, then click [Start Deletion].",
        'progress_status_fmt': "Progress: {percent}% ({val}/{total}) | Success: {del_count}, Fail: {fail_count} | Elapsed: {elapsed} | ETR: {remaining}",
        'progress_finished_fmt': "Job Finished - Success: {del_count}, Fail: {fail_count}",
        
        # Dialog Commons & Buttons
        'ok': "OK",
        'cancel': "Cancel",
        'yes': "Yes",
        'no': "No",
        'pass_use_none': "Do Not Use",
        
        # Input Validation Errors
        'err_title': "Input Error",
        'err_delay_number': "Delay inputs can only accept positive integers!",
        'err_token_empty': "Discord Auth Token is strictly required!",
        'err_guild_empty': "Server ID is required!\nFor personal DMs, enter @me.",
        'err_channel_empty': "Channel ID is required!",
        
        # Password Popups
        'pass_err_title': "Password Error",
        'pass_len_error': "The password must be at least 8 characters for security. Encryption skipped.",
        'pass_len_error_exit': "The password must be at least 8 characters. Aborting execution.",
        'pass_cancel_warn': "Password setup cancelled. Token automatic protection postponed.",
        'pass_cancel_exit': "Master password setup is required. Terminating application.",
        'pass_verify_success': "Password verification successful. Discord token restored.",
        'pass_verify_fail_fmt': "Incorrect password. (Attempts left: {left})",
        'pass_destroy_title': "Permanent Data Destruction",
        'pass_destroy_msg': "3 consecutive incorrect passwords entered. Saved token has been permanently deleted for safety!",
        'pass_token_skip_warn': "Password prompt skipped. Token saving postponed.",
        'pass_crypt_err': "Failure during token encryption: {e}",
        'pass_config_err': "[Warning] Could not save settings to config.json: {e}",
        'pass_block_err': "Access blocked without successful master password authentication.",
        'pass_plain_warn_title': "Plaintext Storage Warning",
        'pass_plain_warn_msg': "If you do not set a password, the token will be stored in plaintext and may be vulnerable to security risks.\nDo you really want to proceed without a password?",
        'status_encrypted': "Security: Encryption Enabled (AES-256-GCM)",
        'status_plaintext': "Security: Encryption Disabled (Plaintext - Vulnerable)",
        
        # Password Modal Dialog Labels
        'dlg_set_title': "New Master Password Setup",
        'dlg_enter_title': "Enter Master Password",
        'dlg_set_desc': "Setup a new master password to secure your local token. (Min 8 chars)",
        'dlg_enter_desc': "Enter the master password to safely decrypt your saved Discord token.",
        'dlg_pass_label': "Password Input",
        'dlg_warn_caps': "* Warning: Caps Lock is currently ON.",
        'dlg_warn_ko': "* Warning: Hangul/English mode is active. Korean characters might be typed.",
        
        # Auto-fetch related messages
        'btn_load_guilds': "Fetch Servers",
        'combo_guild_placeholder': "--- Select Server ---",
        'combo_channel_placeholder': "--- Select Channel ---",
        'dm_display_name': "👤 Direct Messages (@me)",
        'log_fetch_guilds_start': "Fetching guild list...",
        'log_fetch_guilds_success': "Successfully fetched {count} guilds.",
        'log_fetch_channels_success': "Successfully fetched {count} channels.",
        'err_token_required_for_fetch': "Discord token is required to fetch servers!",
        'err_fetch_failed': "Failed to fetch server/channel list: {e}",
        
        # Log Messages
        'log_easy_login_start': "Launching Discord easy login window. Log in to automatically extract your token.",
        'log_easy_login_success': "Successfully extracted login token!",
        'log_easy_login_cancel': "Discord easy login was not completed or was cancelled.",
        'log_easy_login_err': "Failed to launch easy login: {e}",
        'err_easy_login_install': "The 'pywebview' library is required for easy login. Installing automatically...",
        'log_search_author': "Author ID was not provided. Querying account details for your user ID...",
        'log_author_auto_set': "Automatically fetched and applied your account ID: {my_id}",
        'log_author_fail': "Failed to auto-fetch account ID (Status: {status}). Deletion will run based on all authors.",
        'log_author_net_err': "Network error during account ID query: {e}",
        'log_stop_cmd': "Stop command sent. Operation will abort after the current message is processed...",
        'log_pass_destroy': "Saved token permanently destroyed from disk due to 3 password failures.",
        'log_pass_destroy_err': "Error during token destruction: {ex}",
        'log_pass_no_exist': "[Notice] No master password set. Initiating master password setup for token safety.",
        'log_pass_init_ok': "Master password setup complete. Token will be automatically encrypted and saved.",
        
        # Confirmation Popups
        'confirm_exit_title': "Confirm Exit",
        'confirm_exit_msg': "A message deletion job is currently running.\nDo you want to force abort and exit?",
        'confirm_start_title': "Confirm Deletion",
        
        # Help window
        'help_title': "💡 Discord Identity Retrieval Guide",
        'help_tab1': " How to get Auth Token ",
        'help_tab2': " How to get Server & Channel IDs ",
        'help_tab3': " Date Ranges & Filters Guidelines ",
        
        'help_text_token': (
            "■ How to copy your Discord Auth Token (Authorization Token)\n\n"
            "The authorization token is your unique account authentication key.\n"
            "⚠️ IMPORTANT: Sharing this token with others will give them full access to your account!\n\n"
            "--------------------------------------------------------------------------------\n\n"
            "1. Open Chrome or Edge browser on your PC and log in to Discord Web (discord.com/app).\n\n"
            "2. Press [F12] or right-click and choose [Inspect] to open Developer Tools.\n\n"
            "3. Click on the [Network] tab at the top of the Developer Tools panel.\n\n"
            "4. In the Filter box, type '/messages'.\n\n"
            "5. Click on any chat channel in Discord or send a message to trigger network activity.\n\n"
            "6. In the network list, click on the newly appeared 'messages' request.\n\n"
            "7. Select the [Headers] tab on the right side of the details pane.\n\n"
            "8. Scroll down to the [Request Headers] section.\n\n"
            "9. Find 'Authorization' header and copy the long sequence of alphanumeric text next to it.\n\n"
            "10. Paste the copied token into the 'Discord Auth Token' input field of the dashboard."
        ),
        'help_text_ids': (
            "■ How to obtain Discord Server and Channel IDs\n\n"
            "To copy unique identification numbers (IDs), you must enable 'Developer Mode' in Discord first.\n\n"
            "--------------------------------------------------------------------------------\n\n"
            "1. Click the gear icon [User Settings] at the bottom left of the Discord window.\n\n"
            "2. Scroll down the left sidebar and select the [Advanced] menu under App Settings.\n\n"
            "3. Turn on the [Developer Mode] toggle switch at the top.\n\n"
            "4. Close the Settings and return to the chat screen.\n\n"
            "5. [Copy Server ID]:\n"
            "   - Right-click on the server circular icon on the left sidebar.\n"
            "   - Click [Copy ID] at the bottom and paste it into the 'Server ID' field.\n"
            "   ※ If you want to wipe DMs (Direct Messages), type '@me' in the Server ID field.\n\n"
            "6. [Copy Channel ID]:\n"
            "   - Right-click on the specific text channel name.\n"
            "   - Click [Copy ID] at the bottom and paste it into the 'Channel ID' field.\n"
            "   - You can enter multiple channels by separating them with commas (e.g. 12345,67890)."
        ),
        'help_text_filters': (
            "■ Date Range Quick Fill & High-Performance Filter Options\n\n"
            "This utility supports specific query filters to let you clean up only unwanted messages.\n\n"
            "--------------------------------------------------------------------------------\n\n"
            "1. [Date Range Limits & Combobox Auto-Fill]\n"
            "   - 'Start Date' and 'End Date' accept direct Snowflake IDs or can be automatically filled using the dropdown values (e.g. '1 day ago', '1 week ago') calculated from the application runtime.\n"
            "   - Only messages created after the Start Range and before the End Range will be targeted.\n\n"
            "2. [Text Query & Regular Expression Filters]\n"
            "   - Text Query: Targets only messages containing the specific keyword.\n"
            "   - Regex Matching: Filters complex text patterns (e.g. email patterns, phone numbers) for targeted removal.\n\n"
            "3. [File & Link Detection Filters]\n"
            "   - 'Only delete messages containing Links': Keeps normal conversations but wipes messages containing URLs.\n"
            "   - 'Only delete messages containing Files': Wipes images, documents, and ZIP files to restore server space.\n\n"
            "4. [Pinned Messages Protection]\n"
            "   - By default, messages pinned inside the channel are protected from deletion.\n"
            "   - If you wish to wipe pinned messages as well, check the 'Also delete Pinned messages' option.\n\n"
            "5. [API Rate Limit Bypass Delay]\n"
            "   - Search and delete request intervals are configured in milliseconds (ms).\n"
            "   - To prevent IP blocks or account restrictions, it is highly recommended to use the default random delay (1500ms to 3000ms)."
        ),
        
        # Engine Log English Translations
        'log_engine_delay': "-> Random bypass delay: {val:.2f}s",
        'log_engine_search_http_err': "Search HTTP request exception: {e}",
        'log_engine_indexing': "Discord server is indexing search data. Retrying in {retry_after}s...",
        'log_engine_rate_limit_search': "Search API rate limit reached! Retrying in {wait_time}s with increased delay...",
        'log_engine_search_fail': "Message search failed! API Response: {status}, Body: {err}",
        'log_engine_regex_fail': "Regex pattern filtering failed: {e}",
        'log_engine_delete_http_err': "Message delete request error: {e}",
        'log_engine_rate_limit_delete': "Delete API rate limit reached! Retrying in {retry_after}s, forcing delay range to {w}ms ~ {w+1500}ms...",
        'log_engine_archive_thread': "Thread is archived and cannot be deleted. Skipping by increasing offset.",
        'log_engine_delete_fail': "Delete error! API Status: {status}, Detail: {text}",
        'log_engine_stop_user': "Deletion process stopped by user.",
        'log_engine_info_fmt': "[{del_count}/{total}] Created: {time} | Author: {username} | Content: {content} (ID: {id})",
        'log_engine_retry': "Retry deletion delay: {delay}s... ({attempt}/{max_attempt})",
        'log_engine_consecutive_fails': "Delete failures reached 5 consecutively. Please check your token or network. Aborting for safety.",
        'log_engine_running': "Engine is already running.",
        'log_engine_started': "Deletion process started. (Start time: {time})",
        'log_engine_params': "Parameters - Author ID: {author_id}, Guild ID: {guild_id}, Channel ID: {channel_id}",
        'log_engine_fetching': "Fetching messages via API...",
        'log_engine_loop_err': "Loop aborted abnormally (Error: {e})",
        'log_engine_summary': "Grand Total: {total} | Current Page: {found} | Target: {to_delete} | Skipped: {skipped} | Offset: {offset}",
        'log_engine_stats_delay': "Delay settings - Random delete range: {min_d}ms ~ {max_d}ms, Search delay: {search}ms",
        'log_engine_stats_ping': "Ping: {ping}ms, Average Ping: {avg_ping}ms",
        'log_engine_stats_throttled': "Throttled count: {count}, Cumulative wait time: {time}",
        'log_engine_etr': "ETR: {etr}",
        'log_engine_confirm_msg': "Found about {total} messages.\nDo you approve and want to proceed? (ETR: {etr})\n\n---- Preview (Max 5) ----\n{preview}",
        'log_engine_confirm_cancel': "User cancelled deletion at confirmation dialog.",
        'log_engine_skip_page': "No messages to delete on current page. Skipping to next page by modifying range. (Offset: {old} -> {new})",
        'log_engine_api_end': "Reached end of search results. (API returned empty page)",
        'log_engine_empty_retry': "Search result is empty. Retrying search... ({attempt}/{max_attempt})",
        'log_engine_next_page': "Waiting for next search query: {delay}s...",
        'log_engine_finished': "Deletion process finished completely. (End time: {time})",
        'log_engine_time_summary': "Total duration: {time} | Success: {del_count} | Fail: {fail_count}",
        'log_engine_batch_setup': "Configuring batch deletion for {count} channels.",
        'log_engine_batch_start': ">>> Starting batch job ({idx}/{total}) - Channel ID: {channel_id}",
        'log_engine_batch_finished': "All batch channel jobs finished."
    }
}

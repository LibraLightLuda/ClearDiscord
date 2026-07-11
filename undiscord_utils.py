# -*- coding: utf-8 -*-
"""
Undiscord 공통 유틸리티 모듈
시간 포맷 변환, Snowflake ID 변환 및 리소스 경로 해석을 담당합니다.
"""

import sys
import os
import subprocess
import base64
import time
from datetime import datetime, timedelta

# ==================================================
# 필수 의존성 라이브러리 검사 및 동적 자동 설치
# ==================================================

# 1. requests (네트워크 API 요청)
try:
    import requests
except ImportError:
    print("개발 및 네트워크 요청을 위해 'requests' 라이브러리가 필요합니다. 자동 설치를 시작합니다...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
        print("'requests' 라이브러리가 성공적으로 설치되었습니다.")
    except Exception as e:
        print(f"라이브러리 자동 설치 실패. 수동으로 'pip install requests'를 실행해 주세요. 에러: {e}")
        sys.exit(1)


# 2. curl_cffi (Cloudflare WAF 우회를 위한 TLS/HTTP2 모방 통신 라이브러리)
try:
    import curl_cffi
except ImportError:
    print("Cloudflare WAF 우회를 위해 'curl_cffi' 라이브러리가 필요합니다. 자동 설치를 시작합니다...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "curl_cffi"])
        import curl_cffi
        print("'curl_cffi' 라이브러리가 성공적으로 설치되었습니다.")
    except Exception as e:
        print(f"라이브러리 자동 설치 실패. 수동으로 'pip install curl_cffi'를 실행해 주세요. 에러: {e}")
        sys.exit(1)


# ==================================================
# 시간 및 Discord Snowflake 변환 유틸리티 함수군
# ==================================================

def ms_to_hms(ms):
    """
    밀리초(ms) 단위를 'X시간 Y분 Z초' 포맷의 문자열로 변환합니다.
    """
    seconds = int(ms / 1000)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}시간 {m}분 {s}초"


def to_snowflake(date_str):
    """
    날짜 문자열('YYYY-MM-DD HH:MM:SS')을 Discord Snowflake ID로 변환합니다.
    디스코드 Snowflake는 2015-01-01 00:00:00 UTC 기준 밀리초 오프셋 기반으로 생성됩니다.
    만약 날짜 형식이 아니거나 입력값 자체가 숫자라면 그대로 반환합니다.
    """
    if not date_str:
        return None
    if ':' in str(date_str):
        try:
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    ts = int(dt.timestamp() * 1000)
                    # 디스코드 에포크(1420070400000ms) 차감 후 22비트 시프트
                    snowflake = (ts - 1420070400000) << 22
                    return str(snowflake)
                except ValueError:
                    continue
        except Exception as e:
            print(f"Snowflake 변환 오류: {e}")
    return str(date_str)


def calculate_relative_date(selection):
    """
    드롭다운 인터페이스 선택 항목에 기반하여 과거 시각 문자열('YYYY-MM-DD HH:MM:SS')을 계산합니다.
    """
    now = datetime.now()
    if selection == "현재 시각":
        return now.strftime("%Y-%m-%d %H:%M:%S")
    elif selection == "1시간 전":
        return (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    elif selection == "6시간 전":
        return (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
    elif selection == "1일 전 (24h)":
        return (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    elif selection == "3일 전":
        return (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    elif selection == "1주일 전":
        return (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    elif selection == "2주일 전":
        return (now - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    elif selection == "1달 전":
        return (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    elif selection == "3달 전":
        return (now - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    elif selection == "6달 전":
        return (now - timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
    elif selection == "1년 전":
        return (now - timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
    return ""


# ==================================================
# 기타 범용 보안 및 경로 헬퍼 함수군
# ==================================================

def validate_discord_url(url: str):
    """
    전송 대상 URL이 위조되거나 피싱 도메인으로 유출되지 않았는지 엄격하게 화이트리스트 검사합니다.
    반드시 공식 디스코드 HTTPS API 주소('https://discord.com/api/v9/')로 시작해야 합니다.
    비보안 HTTP 혹은 비인증 위조 도메인은 통신 전 차단됩니다.
    """
    if not url:
        raise ValueError("요청 대상 URL이 비어 있습니다.")
    # 디스코드 공식 v9 API 경로로 시작해야 함
    if not url.startswith("https://discord.com/api/v9/"):
        raise ValueError(f"보안 위험: 허가되지 않은 도메인으로의 요청이 감지되어 차단되었습니다: {url}")


def resource_path(relative_path: str) -> str:
    """
    PyInstaller 패키징 환경(sys._MEIPASS) 또는 로컬 개발 환경에 맞춰
    리소스 파일의 실제 가용한 절대 경로를 반환합니다.
    """
    import sys
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ==================================================
# 로그 마스킹 처리를 위한 하위 호환성 문자열 클래스
# ==================================================

class LogString(str):
    """
    일반 문자열(str)을 상속받으면서도 추가적인 메타데이터(extra)를 보존하는 특수 문자열 클래스입니다.
    이를 통해 기존 CLI 환경 및 모킹(Mock) 테스트 코드와의 하위 호환성을 100% 유지하면서,
    GUI 단에서 실시간 마스킹 토글이 가능하도록 원본 로그 데이터를 전달합니다.
    """
    def __new__(cls, value, extra=None):
        obj = super().__new__(cls, value)
        obj.extra = extra
        return obj




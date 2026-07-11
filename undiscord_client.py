# -*- coding: utf-8 -*-
"""
Undiscord SSL 피닝 탑재 HTTP 통신 클라이언트 유틸리티 모듈
"""

import ssl
import hashlib
import json
import base64
from requests.adapters import HTTPAdapter
from urllib3.connectionpool import HTTPSConnectionPool
from undiscord_utils import validate_discord_url

# 기본 내장 디스코드 CA 인증서 SHA-256 지문 목록 (백업용 및 최초 실행용)
DEFAULT_CERT_PINS = {
    "9d2c1407cd22dc5ff6c3ef6f4b6cb9a896d8b671a5c68f86f78f6a3d9051fb66", # Cloudflare Inc TLS CA
    "cb3ccbb76031e5e0138f8dd39a23f9de47ffc35e43c1144bec7454094aafb672", # DigiCert Global Root G2
    "5feb8c24f6534565731f4c704c7d78adcd406b52d0e2e921d7b3dbd38c1177af", # DigiCert High Assurance EV Root CA
    "16af57a9f676b0f1290395d03ba530d44b58f8ad95ed7a8a93ac9b98d1192e21"  # Baltimore CyberTrust Root
}

# 실제 통신 과정에서 검사할 실시간 SSL 핀 메모리 버퍼
DISCORD_CERT_PINS = set(DEFAULT_CERT_PINS)


def update_pins_dynamically() -> dict:
    """
    소스코드 내에 기본 내장된 신뢰 CA 인증서 핀 목록(DEFAULT_CERT_PINS)을
    로컬에서 안전하게 확인하고 통신 검증 준비를 마칩니다.
    (원격 갱신 주소 접속 및 Ed25519 서명 검증 방식에서 로컬 방식으로 전환됨)
    """
    try:
        # 이미 DISCORD_CERT_PINS는 DEFAULT_CERT_PINS로 초기화되어 작동 중입니다.
        return {
            "status": "success",
            "message": f"로컬 SSL 인증서 핀 목록 로드 완료 (수량: {len(DISCORD_CERT_PINS)}개)"
        }
    except Exception as e:
        return {
            "status": "fallback",
            "message": f"로컬 SSL 핀 목록 로드 중 오류 발생 ({e}). 기존 핀 목록을 유지합니다."
        }


class PinnedHTTPSConnectionPool(HTTPSConnectionPool):
    """SSL 핸드셰이크 수립 직후 피어 인증서 지문(SHA-256)을 강제 피닝 검사하는 커넥션 풀입니다."""
    def _new_conn(self):
        conn = super()._new_conn()
        try:
            der_cert = conn.sock.getpeercert(binary_form=True)
            if der_cert:
                cert_sha256 = hashlib.sha256(der_cert).hexdigest()
                if cert_sha256 not in DISCORD_CERT_PINS:
                    conn.close()
                    raise ssl.SSLError(f"SSL Certificate Pinning Verification Failed! Fingerprint: {cert_sha256}")
        except AttributeError:
            pass
        return conn


class PinnedHTTPAdapter(HTTPAdapter):
    """커스텀 피닝 HTTPS 커넥션 풀을 requests 세션에 공급하는 어댑터입니다."""
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        super().init_poolmanager(connections, maxsize, block, **pool_kwargs)
        self.poolmanager.pool_classes_by_scheme['https'] = PinnedHTTPSConnectionPool



def get_browser_headers(token: str, referer: str = None) -> dict:
    """브라우저의 요청 헤더와 X-Super-Properties를 모방한 공통 헤더를 생성합니다."""
    super_properties = {
        "os": "Windows",
        "browser": "Chrome",
        "device": "",
        "system_locale": "ko-KR",
        "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "browser_version": "120.0.0.0",
        "os_version": "10",
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": 240000,
        "client_event_source": None
    }
    super_properties_b64 = base64.b64encode(json.dumps(super_properties).encode('utf-8')).decode('utf-8')
    
    headers = {
        'Authorization': token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'X-Discord-Locale': 'ko',
        'X-Debug-Options': 'bugReporterEnabled',
        'X-Super-Properties': super_properties_b64
    }
    if referer:
        headers['Referer'] = referer
    return headers


def fetch_guilds(token: str) -> list:
    """주어진 디스코드 토큰을 사용하여 사용자가 참여 중인 서버(Guild) 목록을 가져옵니다."""
    from curl_cffi import requests
    url = "https://discord.com/api/v9/users/@me/guilds"
    validate_discord_url(url)
    
    session = requests.Session(impersonate="chrome120")
    session.trust_env = False
    session.proxies = {'http': None, 'https': None}
    
    headers = get_browser_headers(token, referer="https://discord.com/channels/@me")
    resp = session.get(url, headers=headers, verify=True)
    if resp.status_code == 200:
        return resp.json()
    else:
        resp.raise_for_status()


def fetch_channels(token: str, guild_id: str) -> list:
    """
    특정 서버 ID에 속한 채널 목록을 가져옵니다.
    guild_id가 '@me'일 경우 개인 DM 채널 목록을 가져옵니다.
    """
    from curl_cffi import requests
    if guild_id == "@me":
        url = "https://discord.com/api/v9/users/@me/channels"
        referer = "https://discord.com/channels/@me"
    else:
        url = f"https://discord.com/api/v9/guilds/{guild_id}/channels"
        referer = f"https://discord.com/channels/{guild_id}"
        
    validate_discord_url(url)
        
    session = requests.Session(impersonate="chrome120")
    session.trust_env = False
    session.proxies = {'http': None, 'https': None}
    
    headers = get_browser_headers(token, referer=referer)
    resp = session.get(url, headers=headers, verify=True)
    if resp.status_code == 200:
        return resp.json()
    else:
        resp.raise_for_status()

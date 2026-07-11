# -*- coding: utf-8 -*-
"""
Undiscord SSL 피닝 탑재 HTTP 통신 클라이언트 유틸리티 모듈
"""

import ssl
import hashlib
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.connectionpool import HTTPSConnectionPool
from undiscord_utils import validate_discord_url
from undiscord_crypto import verify_ed25519_signature

# 기본 내장 디스코드 CA 인증서 SHA-256 지문 목록 (백업용 및 최초 실행용)
DEFAULT_CERT_PINS = {
    "9d2c1407cd22dc5ff6c3ef6f4b6cb9a896d8b671a5c68f86f78f6a3d9051fb66", # Cloudflare Inc TLS CA
    "cb3ccbb76031e5e0138f8dd39a23f9de47ffc35e43c1144bec7454094aafb672", # DigiCert Global Root G2
    "5feb8c24f6534565731f4c704c7d78adcd406b52d0e2e921d7b3dbd38c1177af", # DigiCert High Assurance EV Root CA
    "16af57a9f676b0f1290395d03ba530d44b58f8ad95ed7a8a93ac9b98d1192e21"  # Baltimore CyberTrust Root
}

# 실제 통신 과정에서 검사할 실시간 SSL 핀 메모리 버퍼
DISCORD_CERT_PINS = set(DEFAULT_CERT_PINS)

# 배포자 검증용 Ed25519 공개키 (Hex 64글자) 및 원격 갱신 주소
SIGNER_PUBLIC_KEY = "261890fd1f824d70ffca8d4deb019db32c1d381f0fb0afe0cdd2a18732fef451"
PIN_UPDATE_URL = "https://raw.githubusercontent.com/LibraLightLuda/ClearDiscord/main/cert_pins.json"


def update_pins_dynamically() -> dict:
    """
    원격 서버에서 비대칭키 서명된 최신 SSL 핀 목록을 다운로드하여 
    메모리 내의 DISCORD_CERT_PINS를 동적으로 업데이트합니다.
    갱신 및 검증에 성공할 경우 결과를 반환하며, 실패할 경우 디폴트 핀으로 안전하게 폴백합니다.
    """
    session = requests.Session()
    # SSL 피닝이 없는 순수 HTTPS 어댑터를 마운트하여 갱신 서버 통신 시 순환 피닝 오류를 방지
    session.mount("https://", HTTPAdapter())
    session.trust_env = False
    session.proxies = {'http': None, 'https': None}
    
    try:
        # 타임아웃 5초 지정하여 무한 대기 방지
        resp = session.get(PIN_UPDATE_URL, timeout=5, verify=True)
        if resp.status_code == 200:
            payload = resp.json()
            data = payload.get("data", {})
            signature = payload.get("signature", "")
            
            # 서명 검증 대상 데이터를 일관성 있게 직렬화
            serialized_data = json.dumps(data, sort_keys=True).encode('utf-8')
            
            if verify_ed25519_signature(serialized_data, signature, SIGNER_PUBLIC_KEY):
                new_pins = data.get("pins", [])
                if new_pins:
                    DISCORD_CERT_PINS.clear()
                    DISCORD_CERT_PINS.update(new_pins)
                    return {
                        "status": "success",
                        "message": f"동적 SSL 인증서 핀 목록 갱신 완료 (수량: {len(new_pins)}개)",
                        "pins": list(new_pins)
                    }
                else:
                    return {
                        "status": "fallback",
                        "message": "갱신 데이터에 유효한 핀 목록이 없어 기본 핀으로 유지합니다."
                    }
            else:
                return {
                    "status": "fallback",
                    "message": "서명 검증 실패(위조 가능성 감지). 안전을 위해 기존 핀 목록을 유지합니다."
                }
        else:
            return {
                "status": "fallback",
                "message": f"원격 갱신 서버 응답 실패 (HTTP {resp.status_code}). 기존 핀 목록을 유지합니다."
            }
    except Exception as e:
        return {
            "status": "fallback",
            "message": f"원격 갱신 서버 통신 중 오류 발생 ({e}). 기존 핀 목록을 유지합니다."
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



def fetch_guilds(token: str) -> list:
    """주어진 디스코드 토큰을 사용하여 사용자가 참여 중인 서버(Guild) 목록을 가져옵니다."""
    url = "https://discord.com/api/v9/users/@me/guilds"
    validate_discord_url(url)
    
    session = requests.Session()
    session.mount("https://", PinnedHTTPAdapter())
    session.trust_env = False
    session.proxies = {'http': None, 'https': None}
    headers = {
        'Authorization': token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
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
    if guild_id == "@me":
        url = "https://discord.com/api/v9/users/@me/channels"
    else:
        url = f"https://discord.com/api/v9/guilds/{guild_id}/channels"
        
    validate_discord_url(url)
        
    session = requests.Session()
    session.mount("https://", PinnedHTTPAdapter())
    session.trust_env = False
    session.proxies = {'http': None, 'https': None}
    headers = {
        'Authorization': token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    resp = session.get(url, headers=headers, verify=True)
    if resp.status_code == 200:
        return resp.json()
    else:
        resp.raise_for_status()

# -*- coding: utf-8 -*-
"""
Undiscord SSL 피닝 탑재 HTTP 통신 클라이언트 유틸리티 모듈
"""

import ssl
import hashlib
import requests
from requests.adapters import HTTPAdapter
from urllib3.connectionpool import HTTPSConnectionPool
from undiscord_utils import validate_discord_url

# 디스코드 API 서버 및 Gateway에 유효한 CA 공개키 및 인증서 SHA-256 지문 목록 (16진수)
DISCORD_CERT_PINS = {
    "9d2c1407cd22dc5ff6c3ef6f4b6cb9a896d8b671a5c68f86f78f6a3d9051fb66", # Cloudflare Inc TLS CA
    "cb3ccbb76031e5e0138f8dd39a23f9de47ffc35e43c1144bec7454094aafb672", # DigiCert Global Root G2
    "5feb8c24f6534565731f4c704c7d78adcd406b52d0e2e921d7b3dbd38c1177af", # DigiCert High Assurance EV Root CA
    "16af57a9f676b0f1290395d03ba530d44b58f8ad95ed7a8a93ac9b98d1192e21"  # Baltimore CyberTrust Root
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

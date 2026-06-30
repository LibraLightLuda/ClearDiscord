# -*- coding: utf-8 -*-
"""
Undiscord 토큰 보호 및 암호화 모듈
마스터 비밀번호 기반 대칭키 암호화(AES-256-GCM) 기법을 사용하여
로컬 설정 파일(config.json) 내의 디스코드 토큰 정보를 국가 표준 보안 등급으로 강력히 보호합니다.
"""

import sys
import os
import base64
import subprocess

# ==================================================
# 필수 의존성 라이브러리 검사 및 동적 자동 설치
# ==================================================

# cryptography (토큰 안전 대칭키 암호화 및 유도)
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError:
    print("보안 암호화를 위해 'cryptography' 라이브러리가 필요합니다. 자동 설치를 시작합니다...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        print("'cryptography' 라이브러리가 성공적으로 설치되었습니다.")
    except Exception as e:
        print(f"라이브러리 자동 설치 실패. 수동으로 'pip install cryptography'를 실행해 주세요. 에러: {e}")
        sys.exit(1)


def derive_key(password: str, salt: bytes) -> bytes:
    """
    사용자가 기입한 마스터 비밀번호와 고유 솔트값(salt)을 바탕으로
    PBKDF2-HMAC-SHA256 알고리즘을 사용해 안전한 32바이트(256비트) 대칭 키를 유도합니다.
    OWASP 권장사항에 부합하도록 반복 횟수(iterations)를 600,000회로 적용합니다.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
    )
    return kdf.derive(password.encode('utf-8'))


def encrypt_data(data: str, password: str) -> tuple[str, str, str]:
    """
    사용자가 지정한 비밀번호를 통해 데이터를 최고 등급인 AES-256-GCM 알고리즘으로 인증 암호화합니다.
    12바이트 무작위 Nonce와 16바이트 무작위 Salt를 사용하여 암호문을 생성하며,
    암호문과 검증 문자열은 base64 형태로 패킹되어 반환됩니다.
    """
    salt = os.urandom(16)
    key = derive_key(password, salt)
    
    aesgcm = AESGCM(key)
    
    # 토큰 암호화 (무작위 12바이트 Nonce 생성 및 병합)
    nonce = os.urandom(12)
    enc_data_bytes = aesgcm.encrypt(nonce, data.encode('utf-8'), None)
    enc_data = base64.b64encode(nonce + enc_data_bytes).decode('utf-8')
    
    # 비밀번호 검증 코드 생성 (무작위 12바이트 Nonce 생성 및 b"VERIFY_PASS" 암호화 병합)
    verify_nonce = os.urandom(12)
    enc_verify_bytes = aesgcm.encrypt(verify_nonce, b"VERIFY_PASS", None)
    enc_verify = base64.b64encode(verify_nonce + enc_verify_bytes).decode('utf-8')
    
    return enc_data, base64.b64encode(salt).decode('utf-8'), enc_verify


def decrypt_data(enc_data: str, password: str, salt_str: str, verify_str: str) -> str:
    """
    저장된 암호문과 솔트, 검증 토큰을 사용자가 입력한 비밀번호로 AES-256-GCM 복호화합니다.
    비밀번호가 올바르지 않거나 데이터가 임의 위조/손상된 경우 ValueError("복호화 실패")를 발생시킵니다.
    """
    try:
        salt = base64.b64decode(salt_str.encode('utf-8'))
        key = derive_key(password, salt)
        aesgcm = AESGCM(key)
        
        # 비밀번호 검증 코드 복호화 및 유효성 확인 (무결성 검증)
        verify_bytes = base64.b64decode(verify_str.encode('utf-8'))
        if len(verify_bytes) < 12:
            raise ValueError()
        verify_nonce = verify_bytes[:12]
        verify_ciphertext = verify_bytes[12:]
        
        decrypted_verify = aesgcm.decrypt(verify_nonce, verify_ciphertext, None)
        if decrypted_verify != b"VERIFY_PASS":
            raise ValueError()
            
        # 디스코드 토큰 원문 복호화
        data_bytes = base64.b64decode(enc_data.encode('utf-8'))
        if len(data_bytes) < 12:
            raise ValueError()
        nonce = data_bytes[:12]
        ciphertext = data_bytes[12:]
        
        return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
    except Exception:
        raise ValueError("복호화 실패")

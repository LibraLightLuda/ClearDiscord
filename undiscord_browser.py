# -*- coding: utf-8 -*-
"""
Undiscord 브라우저 탐색 및 실행 유틸리티 모듈

사용자 시스템에 설치된 웹 브라우저(Google Chrome, Microsoft Edge, Mozilla Firefox)를 탐색하고,
간편 로그인 구동 실패 시 대체 수단으로 지정 브라우저를 구동시켜 로그인할 수 있도록 돕습니다.
"""

import os
import sys
import subprocess
import webbrowser

# Windows 환경에 대응하기 위해 winreg 모듈을 임포트합니다.
if sys.platform == 'win32':
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None


def find_browser_path(browser_key):
    """
    Windows 레지스트리 및 기본 설치 디렉토리에서 특정 브라우저의 실행 파일 경로를 탐색합니다.
    
    :param browser_key: 탐색할 브라우저 키명 ('chrome', 'msedge', 'firefox')
    :return: 브라우저 실행 파일의 절대 경로 (찾지 못한 경우 None)
    """
    if sys.platform != 'win32':
        # Windows가 아닌 플랫폼에서는 webbrowser 모듈에 탐색을 위임합니다.
        return None

    # 1단계: Windows 레지스트리 App Paths에서 실행 파일 경로 탐색 (가장 정확한 방법)
    # 시스템 레지스트리와 32비트 에뮬레이션(WOW6432Node) 키를 모두 순회합니다.
    reg_subkeys = [
        rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{browser_key}.exe",
        rf"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\{browser_key}.exe"
    ]
    
    if winreg:
        for subkey in reg_subkeys:
            for root_key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(root_key, subkey) as key:
                        # 기본값(이름이 빈 문자열)을 가져오면 실행 파일 경로가 리턴됩니다.
                        path, _ = winreg.QueryValueEx(key, "")
                        if path and os.path.exists(path):
                            return path
                except Exception:
                    continue

    # 2단계: 레지스트리에서 찾지 못했거나 접근이 제한된 경우, 알려진 기본 설치 경로에서 수동 탐색
    paths_dict = {
        'chrome': [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe")
        ],
        'msedge': [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ],
        'firefox': [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Mozilla Firefox\firefox.exe")
        ]
    }

    if browser_key in paths_dict:
        for candidate_path in paths_dict[browser_key]:
            if candidate_path and os.path.exists(candidate_path):
                return candidate_path

    return None


def get_available_browsers():
    """
    현재 사용자 컴퓨터에 설치되어 사용 가능한 브라우저 목록을 딕셔너리 형태로 반환합니다.
    
    :return: {'브라우저이름': '실행파일경로'} 구조의 딕셔너리
    """
    targets = {
        'chrome': 'Google Chrome',
        'msedge': 'Microsoft Edge',
        'firefox': 'Mozilla Firefox'
    }
    
    available = {}
    for key, name in targets.items():
        path = find_browser_path(key)
        if path:
            available[key] = {
                'name': name,
                'path': path
            }
            
    return available


def launch_browser(browser_key, url="https://discord.com/login"):
    """
    지정한 브라우저 키를 사용하여 특정 URL을 새 창으로 엽니다.
    만약 지정한 브라우저가 없거나 실행에 실패할 경우, 시스템 기본 웹 브라우저(webbrowser)로 폴백합니다.
    
    :param browser_key: 실행할 브라우저 키 ('chrome', 'msedge', 'firefox' 또는 'default')
    :param url: 오픈할 웹페이지 주소
    :return: 브라우저 실행 성공 여부 (bool)
    """
    if browser_key == 'default':
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False

    path = find_browser_path(browser_key)
    if path:
        try:
            # 외부 프로세스로 브라우저를 백그라운드 기동시킵니다.
            subprocess.Popen([path, url])
            return True
        except Exception as e:
            print(f"DEBUG: Failed to launch browser '{browser_key}' via subprocess: {e}", flush=True)

    # 3단계 최종 폴백: 지정된 브라우저가 없거나 실행에 실패하면 시스템 기본 브라우저 모듈을 사용합니다.
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"ERROR: Browser fallback launch failed: {e}", flush=True)
        return False

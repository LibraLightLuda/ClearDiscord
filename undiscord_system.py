# -*- coding: utf-8 -*-
"""
Undiscord 시스템 입력 상태 모듈
Windows OS 환경에서 Caps Lock 및 한영키(한글 입력기) 상태를 감지하여
비밀번호 오입력을 사전에 경고하는 기능들을 제공합니다.
"""

def is_capslock_on() -> bool:
    """
    Windows OS 환경에서 Caps Lock 키의 활성화 상태를 실시간 체크합니다.
    비밀번호 입력 시 대소문자 실수를 경고하기 위해 사용됩니다. Windows가 아닐 경우 False를 반환합니다.
    """
    try:
        import ctypes
        return (ctypes.windll.user32.GetKeyState(0x14) & 0x0001) != 0
    except Exception:
        return False


def is_hangul_mode() -> bool:
    """
    Windows OS 환경에서 현재 활성 창의 IME가 한글 입력 모드인지 체크합니다.
    비밀번호 입력 시 한영키가 켜져 있어 오입력하는 것을 사용자에게 알리기 위해 사용됩니다.
    Windows가 아니거나 상태 확인이 불가할 경우 False를 반환합니다.
    """
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return False
        hwnd_ime = ctypes.windll.imm32.ImmGetDefaultIMEWnd(hwnd)
        if not hwnd_ime:
            return False
        # WM_IME_CONTROL = 0x0283, IMC_GETCONVERSIONMODE = 0x0001
        conversion_mode = ctypes.windll.user32.SendMessageW(hwnd_ime, 0x0283, 0x0001, 0)
        # IME_CMODE_NATIVE (한글) 비트 = 0x0001
        return (conversion_mode & 0x0001) != 0
    except Exception:
        return False

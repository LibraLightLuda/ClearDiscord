# -*- coding: utf-8 -*-
"""
Undiscord 간편 로그인 윈도우 모듈
pywebview 라이브러리를 기동하여 디스코드 로그인 페이지를 노출하고 토큰을 가로챕니다.
"""

import sys
import os
import time
import threading
import traceback

def run_login_window():
    """pywebview를 사용하여 디스코드 로그인 페이지를 띄우고 토큰을 자동 추출합니다."""
    try:
        try:
            import webview
        except ImportError:
            # pywebview 자동 설치 시도
            import subprocess
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview"])
                import webview
            except Exception as e:
                print(f"ERROR: pywebview installation failed. {e}\n{traceback.format_exc()}", flush=True)
                sys.exit(1)
        
        token_found = [None]
        
        # 디스코드 보안 차단(reCAPTCHA / Cloudflare) 우회를 위한 최신 Chrome 브라우저 User-Agent 위장
        try:
            user_agent_str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            if 'USER_AGENT' in webview.settings:
                webview.settings['USER_AGENT'] = user_agent_str
            elif 'user_agent' in webview.settings:
                webview.settings['user_agent'] = user_agent_str
            else:
                try:
                    webview.settings['USER_AGENT'] = user_agent_str
                except Exception:
                    webview.settings.update({'USER_AGENT': user_agent_str})
        except Exception as e:
            print(f"DEBUG: Setting user agent failed: {e}", flush=True)
        
        # 창이 완전히 닫혔는지를 안전하게 가로채기 위한 공유 플래그
        window_closed = [False]
        
        def check_token(window):
            # 디스코드 웹 세션 토큰 추출을 위한 복합 JS (iframe LocalStorage 우회 및 Webpack Chunk 듀얼 감지)
            js_code = """
            (function() {
                try {
                    // 기법 1: iframe 생성을 통한 localStorage.token 우회 탈취
                    let iframe = document.createElement('iframe');
                    document.head.append(iframe);
                    let token = iframe.contentWindow.localStorage.token;
                    iframe.remove();
                    if (token) {
                        return token.replace(/"/g, '');
                    }
                } catch (e) {}
                
                try {
                    // 기법 2: Webpack Chunk Injection 방식
                    return (window.webpackChunkdiscord_app.push([
                        [Math.random()],
                        {},
                        (req) => {
                            for (const m of Object.keys(req.c).map((x) => req.c[x].exports)) {
                                if (m && m.default && m.default.getToken !== undefined) {
                                    return m.default.getToken();
                                }
                            }
                        }
                    ]));
                } catch (e) {}
                
                return null;
            })()
            """
            
            # 환경변수 상속을 통한 일회용 IPC 암호화 키 조회
            ipc_key = os.environ.get("ENV_SEC_KEY", "")
            
            while not window_closed[0]:
                try:
                    time.sleep(0.5)
                    # 대기 시간 이후 루프 진입 전 닫힘 여부 재검사
                    if window_closed[0]:
                        break
                    res = window.evaluate_js(js_code)
                    if res and isinstance(res, str) and len(res.strip()) > 30:
                        token_found[0] = res.strip()
                        
                        # 보안 강화: 부모 프로세스에 토큰을 전달할 때 표준 출력을 암호화하여 패킷 가로채기 방지
                        if ipc_key:
                            try:
                                from undiscord_crypto import encrypt_ipc
                                enc_token = encrypt_ipc(token_found[0], ipc_key)
                                print(f"TOKEN_ENC:{enc_token}", flush=True)
                            except Exception as e:
                                print(f"ERROR: IPC encryption failed: {e}", flush=True)
                        else:
                            # 평문 폴백 (하위 호환)
                            print(f"TOKEN:{token_found[0]}", flush=True)
                        
                        # 메모리 보호: 평문 토큰을 메모리상에서 즉각 소거
                        try:
                            from undiscord_crypto import wipe_memory_string
                            wipe_memory_string(token_found[0])
                        except Exception:
                            pass
                        
                        window.destroy()
                        break
                except Exception as ex:
                    # 페이지 리다이렉션 중 일시적인 자바스크립트 실행 예외는 무시하고 감시를 유지합니다.
                    # 단, 창이 수동으로 완전히 닫힌 경우(Exception 메시지에 파괴/닫힘/ObjectDisposed 관련 문구 포함 시) 감시 루프를 즉각 탈출합니다.
                    err_str = str(ex).lower()
                    if window_closed[0] or any(x in err_str for x in ['close', 'destroy', 'null', 'object', 'access', 'denied', 'dispose', '삭제된', '개체']):
                        break
                    continue

        # 반응형 레이아웃 대응 및 QR코드 로그인 영역이 숨겨지지 않도록 창 크기를 가로로 충분히 확장합니다. (width=1000)
        window = webview.create_window(
            title="Discord Easy Login",
            url="https://discord.com/login",
            width=1000,
            height=700,
            resizable=True
        )
        
        # 렌더러 로딩 완료 이전 evaluate_js 호출로 인한 교착 상태 및 프리징 방지를 위해 loaded 이벤트 시점에 스레드 구동
        def on_loaded():
            t = threading.Thread(target=check_token, args=(window,), daemon=True)
            t.start()
            
        def on_closed():
            window_closed[0] = True
            
        window.events.loaded += on_loaded
        window.events.closed += on_closed
        
        # pywebview의 기본 브라우저 시작 구동을 지시합니다. (기본 설정이 최적의 안정성을 보장합니다)
        webview.start()
        
    except Exception as e:
        print(f"ERROR: {e}\n{traceback.format_exc()}", flush=True)
        sys.exit(1)

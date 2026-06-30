# Undiscord Python GUI 패치 내역 (Patch Notes)

본 문서는 파이썬 기반 Undiscord GUI 도구의 최신 패치 및 리팩토링, 보안 최적화 내역을 다른 팀원들과 공유하고 공지하기 위해 기록되었습니다.

---

## 📌 패치 개요
- **버전**: V1.1 (기존 파이썬 이식판 V1.0 기반 기능 개선 및 보안 고도화)
- **주요 목표**: 코드 모듈화, 강력한 선 인증 보안 설계, 패킷 가로채기 및 도메인 하이재킹 차단, UI/UX 최적화

---

## 🛠️ 주요 변경 및 개선 사항

### 1. 소스 코드 모듈화 및 리팩토링 (가독성 및 토큰 절약)
기존 단일 1,500줄 이상의 비대했던 `undiscord_gui.py` 파일을 역할별 논리 단위로 분리하여 코드의 유지보수 효율을 높이고 AI 분석에 효율적인 가벼운 모듈 형태로 분할하였습니다.
- **[undiscord_utils.py](file:///d:/Antigravity/undiscord/undiscord/undiscord_utils.py)**: 의존 라이브러리 자동 설치, Snowflake 변환, 시간 포맷팅, 토큰 보안용 AES 암복호화 및 URL 화이트리스트 검사 전담.
- **[undiscord_core.py](file:///d:/Antigravity/undiscord/undiscord/undiscord_core.py)**: API 호출, Rate Limit 대기 및 메시지 검색/삭제 루프를 관리하는 핵심 엔진 `UndiscordCore` 분리.
- **[undiscord_dialogs.py](file:///d:/Antigravity/undiscord/undiscord/undiscord_dialogs.py)**: 마스터 비밀번호 설정 및 입력을 요구하는 모달 창 `PasswordDialog` 분리.
- **[undiscord_gui.py](file:///d:/Antigravity/undiscord/undiscord/undiscord_gui.py)**: 메인 레이아웃 및 제어 흐름만 남기고 상단 re-export 지정을 통해 기존 단위 테스트 및 모듈들과 100% 호환되도록 구성.

### 2. 비밀번호 선 인증 보안 체계 도입
로컬에 암호화 보존된 토큰 및 기타 설정값이 노출되는 것을 방지하기 위해 프로그램 기동 시 즉각 보호 프로세스를 수행합니다.
- **메인 창 초기 은닉**: 마스터 비밀번호 인증을 완전히 완료하거나 최초 설정을 마칠 때까지 메인 윈도우 창을 화면에 완전히 드러내지 않고 숨김(`withdraw`) 상태로 유지합니다.
- **강제 포커스 및 최상단 노출**: 모달 다이얼로그에 `topmost` 속성과 `focus_force`를 주어 실행 즉시 입력 창이 가장 위로 뜨도록 제어했습니다.
- **인증 성공 시 노출 / 실패 시 완전 차단**: 비밀번호 인증 성공 시에만 메인 창이 복구(`deiconify`)되며, 사용자가 입력을 취소하거나 3회 오류로 영구 파기되는 경우 즉시 프로세스를 파괴(`destroy`)하고 앱을 완전히 강제 종료합니다.

### 3. 고성능 네트워크 패킷 보안 적용 (오버헤드 0%)
통신 속도 저하 없이 패킷 가로채기나 페이크(피싱) 서버 도메인 접근을 차단하는 보안 수칙을 추가했습니다.
- **위조 도메인 방지 (URL 화이트리스트)**: 모든 API 통신 직전 `validate_discord_url` 함수를 강제 통과하여, 목적지 주소가 반드시 공식 디스코드 HTTPS API 주소(`https://discord.com/api/v9/`)로 시작되는지 엄격 검사합니다.
- **만인간 공격(MitM) 프록시 무력화**: `requests` 통신 세션 시 로컬 환경 프록시를 완전히 바이패스하도록 `proxies = {'http': None, 'https': None}` 및 `trust_env = False`를 적용해 패킷 분석/수정 도구의 하이재킹을 방어합니다.
- **명시적 SSL/TLS 유효성 검증 고정**: 모든 요청에 `verify=True` 검증을 강제 고정하여 암호화되지 않은 비보안 통신 유도 공격을 차단합니다.

### 4. UI/UX 레이아웃 최적화
- **창 세로 높이 조정**: 모니터의 DPI 스케일링 배율에 의해 하단 작업 제어 버튼(시작/중단)이 잘려서 보이지 않는 문제를 수정하기 위해 창 세로 크기를 확장 조정했습니다. (기본 `1120x860` 및 최소 `1080x800` 지정)
- **정보 통합형 헤더 디자인**: 최하단 푸터 영역을 완전히 제거하고, 좌측 하단의 로고 설명 란에 만든이 `LibraLight`(디스코드 채널로 연동) 및 오픈소스 원본 저장소 `victornpb/undiscord` 링크를 자연스럽게 결합하여 콤팩트한 구조를 갖추었습니다.

### 5. 작업 속도 유지를 위한 빌드 정책 추가
- **[.agents/AGENTS.md](file:///d:/Antigravity/undiscord/undiscord/.agents/AGENTS.md)**에 맞춤형 규칙을 추가하여, 빌드 테스트 시간으로 인한 응답 지연을 방지하고자 사용자의 명시적인 지시 전에는 PyInstaller 빌드 테스트(`build.bat`)를 구동하지 않도록 영구 설정 및 격리하였습니다.

### 6. 프로그램 및 실행파일 아이콘 적용
- **로컬 이미지 변환**: `cold_icon` 원본 리소스를 PIL(Pillow) 모듈을 이용해 `cold.png` (256x256) 및 `cold.ico` (다중 해상도 아이콘 포맷)로 정격 변환했습니다.
- **Tkinter UI 적용**: Tkinter 윈도우 인스턴스에 `iconphoto`를 사용해 타이틀바 아이콘으로 지정했고, 윈도우 `AppUserModelID`를 ctypes 셸 API를 통해 명시 매칭하여 작업표시줄에 차가운 색상 아이콘이 정상 매핑되도록 처리했습니다.
- **PyInstaller 빌드 탑재**: `build.bat` 스크립트를 변경하여 컴파일된 `UndiscordGUI.exe` 실행파일 자체 아이콘에도 차가운 색상 아이콘(`cold.ico`)이 각인되어 빌드되도록 최종 반영했습니다.


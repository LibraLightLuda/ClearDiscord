[![Total Downloads](https://img.shields.io/github/downloads/LibraLightLuda/ClearDiscord/total)](https://github.com/LibraLightLuda/ClearDiscord/releases)

# 🧹 디스코드 메시지 청소 대시보드 (Undiscord Python GUI)

이 프로그램은 내가 디스코드 채팅방이나 1:1 대화방(DM)에 썼던 과거의 메시지들을 한 번에 안전하고 깨끗하게 지워주는 편리한 개인용 도구입니다.

---

# 🇰🇷 [한국어 설명] 초보자를 위한 상세 이용 설명서

## 💡 이 프로그램은 무엇인가요?
디스코드에서 수많은 대화를 나누다 보면, 옛날에 내가 쓴 글이나 올린 사진들을 한꺼번에 지우고 싶을 때가 있습니다. 하나하나 마우스로 지우려면 시간이 너무 오래 걸립니다. 
이 프로그램은 **내가 지우고 싶은 방을 지정해서 내가 썼던 글들을 자동으로 빠르게 지워주는 청소기**입니다.

> [!WARNING]
> **⚠️ 꼭 읽어주세요! (보안 경고 및 사용자 책임)**
> *   **⚠️ 토큰 노출 금지:** 로그인 열쇠(인증 토큰)는 계정의 비밀번호와 같은 역할을 합니다. **절대 다른 사람에게 공유하거나 스크린샷 등으로 노출하지 마세요.** 토큰이 유출되면 타인이 내 계정을 완전히 지배할 수 있게 됩니다. (혹시라도 유출되었을 경우 즉시 디스코드 비밀번호를 변경하여 기존 토큰을 무효화해야 합니다.)
> *   **🚫 계정 정지 위험:** 디스코드는 자동화 도구(셀프봇 등)의 사용을 공식적으로 금지하고 있습니다. 이 프로그램의 사용으로 인해 디스코드 계정이 영구/일시 정지되거나 제한될 수 있습니다.
> *   **⚖️ 사용자 책임 명시 (Disclaimer):** 이 프로그램을 사용함으로써 발생하는 모든 결과와 손실(계정 정지, 토큰 유출, 데이터 삭제 등)에 대한 책임은 **전적으로 프로그램을 실행한 사용자 본인**에게 있습니다. 개발자는 어떠한 상황에서도 이에 대한 책임을 지지 않습니다. 동의하시는 경우에만 사용해 주십시오.
> *   **💡 권장 사항:** 너무 짧은 시간 동안 많은 글을 연속으로 지우면 감지될 확률이 높습니다. 기본 안전 대기 시간(1.5초~3초)을 유지하시는 것을 강력히 권장합니다.

---

## ✨ 대표적인 편리한 기능들
어려운 기술 용어 대신, 누구나 바로 쓸 수 있는 쉬운 기능들이 준비되어 있습니다.

1.  **비밀번호로 로그인 열쇠 잠금 (안전 보관)**
    *   디스코드에 접속하려면 내 계정의 고유한 "로그인 열쇠(토큰)"가 필요합니다. 이 길고 복잡한 열쇠를 매번 입력할 필요가 없도록 비밀번호를 설정해 안전하게 저장해 둡니다.
    *   보안을 위해 **비밀번호를 3번 연속으로 틀리면**, 저장되어 있던 내 계정 열쇠 정보가 컴퓨터에서 완전히 지워집니다.
2.  **토큰 정보 마스킹 및 화면 노출 차단 (보안 강화)**
    *   대시보드 상에서 로그인 열쇠(토큰)를 입력하거나 가져오는 즉시 `••••••••••••••••`로 숨김 처리하여 주변 노출 및 숄더 서핑 위험을 방지합니다. 한시적으로 보기/숨기기 버튼을 통해 확인할 수 있습니다.
3.  **원하는 대화방 골라 지우기**
    *   내가 참여 중인 서버의 특정 채팅방만 지울 수도 있고, 친구와의 **1:1 개인 대화방**에 내가 쓴 글만 쏙 골라 지울 수도 있습니다.
4.  **지우고 싶은 날짜 범위 지정하기**
    *   "오늘 쓴 글만 지우기", "1주일 전부터 쓴 글만 지우기", "특정 날짜 사이에 쓴 글만 지우기" 등 날짜를 손쉽게 골라 청소할 수 있습니다.
5.  **특정 글만 골라 지우기 (필터)**
    *   특정 단어가 들어간 글만 지우기
    *   사진이나 동영상 파일이 올라간 글만 지우기 (채널 용량 정리용)
    *   링크 주소가 들어간 글만 지우기
6.  **지운 메시지 PC에 백업하기**
    *   디스코드에서 영구 삭제하기 전에, 삭제될 메시지의 원본 내용을 로컬 컴퓨터(`deleted_backups/` 폴더)에 텍스트 형식으로 안전하게 백업 및 저장합니다.
7.  **로그 메시지 내 채팅 내용 마스킹 (개인정보 보호)**
    *   옵션을 켜면 삭제 진행 로그창과 삭제 전 확인 창에서 내 채팅 내용이 `●●● (마스킹됨)` 처리되어 화면을 방송하거나 캡처할 때 개인정보나 대화 내용 유출을 완전히 보호합니다. (백업 파일에는 원본 내용이 그대로 기록됩니다.)
8.  **동적 SSL 피닝 및 Ed25519 서명 검증 (네트워크 보안)**
    *   앱 실행 시 원격 저장소로부터 Ed25519 비대칭키로 전자 서명된 최신 SSL 인증서 지문 목록을 동적으로 내려받아 갱신합니다. 이를 통해 사설 인증서를 통한 네트워크 패킷 도청 및 중간자 공격(MITM)을 원천 차단하며, 검증 실패 시 내장 핀으로 안전하게 자동 폴백(Fallback)합니다.

---

## 🚀 아주 쉬운 3단계 사용 방법

### 1단계: 청소에 필요한 정보(로그인 열쇠 및 방 주소) 준비하기
프로그램이 내가 누군지, 어디를 청소해야 하는지 알 수 있도록 아래 3가지 정보를 미리 알아둬야 합니다.

*   **🔑 내 계정의 로그인 열쇠 (인증 토큰):**
    1. 컴퓨터 브라우저(크롬 등)로 디스코드 사이트에 접속해 로그인합니다.
    2. 키보드 맨 위의 `F12`를 눌러 개발자 도구 창을 엽니다.
    3. 맨 위의 메뉴 중 **네트워크(Network)** 탭을 누릅니다.
    4. 디스코드 채팅창에 아무 글자나 적어 올리거나 방을 클릭합니다.
    5. 개발자 도구 창 리스트에 영어 단어들이 뜨는데, 그중 하나를 누르고 오른쪽 상세 정보에서 `Authorization` 이라는 단어 옆에 있는 길고 복잡한 영어/숫자 글자들을 통째로 복사합니다.
*   **🏠 방 주소 (서버 ID 및 채널 ID):**
    1. 디스코드 앱 설정 -> 고급 -> **개발자 모드**를 켭니다.
    2. 내가 지우고 싶은 서버 아이콘이나 채팅방 이름을 마우스 오른쪽 버튼으로 누르고 맨 아래에 있는 **ID 복사하기**를 누릅니다.
    *   *※ 친구와의 1:1 대화방을 지우고 싶다면, 서버 ID 칸에 **`@me`**를 적고 채널 ID 칸에 대화방 ID를 적으시면 됩니다.*

### 2단계: 프로그램 실행하고 값 입력하기
1.  이 폴더에서 `build.bat` 파일을 더블 클릭하여 빌드된 **`UndiscordGUI.exe`** 파일을 실행하거나, 명령창에 `python undiscord_gui.py`를 입력해 프로그램을 켭니다.
2.  사용할 비밀번호를 설정하고 로그인합니다.
3.  준비한 로그인 열쇠(토큰), 서버 ID, 채널 ID를 빈칸에 적어 넣습니다.

### 3단계: 청소 시작
1.  지우고 싶은 날짜나 단어 등 옵션을 설정합니다. (잘 모르겠다면 기본 설정 그대로 두셔도 됩니다.)
2.  하단의 **[작업 시작]** 버튼을 누릅니다.
3.  안내창이 뜨면 확인을 누릅니다. 실시간으로 로그 창에 글이 지워지는 과정이 표시됩니다.
4.  지우는 중간에 멈추고 싶다면 **[작업 중단]** 버튼을 누르면 안전하게 멈춥니다.

---

# 🇺🇸 [English Explanation] User Guide for Beginners

## 💡 What is this program?
When you use Discord a lot, you might want to delete all your past comments or photos at once. Deleting them one by one manually takes forever.
This program is an **automated Discord message cleaner** that quickly finds and deletes only the messages you wrote in a specific channel or direct message (DM) room.

> [!WARNING]
> **⚠️ Please Read! (Security Warning & Disclaimer)**
> *   **⚠️ Never Share Your Token:** Your authentication token acts as a master key to your account. **Do not share your token or expose it in screenshots/public spaces.** Anyone with access to your token can take full control of your account. (If your token is accidentally leaked, change your Discord password immediately to invalidate it.)
> *   **🚫 Risk of Account Termination:** Discord officially forbids the use of automation tools (self-bots). Using this tool could result in temporary or permanent restriction/suspension of your Discord account.
> *   **⚖️ Disclaimer (Use at Your Own Risk):** You are fully responsible for any actions taken and consequences arising from the use of this tool (including account termination, token leak, or data deletion). The developers assume no liability or responsibility for any damages. Use this tool at your own risk.
> *   **💡 Recommendations:** Attempting to delete messages too quickly increases detection risks. We highly recommend keeping the default safe delay settings (1.5 to 3 seconds).

---

## ✨ Simple and Useful Features
We have translated complex technical features into easy-to-use functions for everyone.

1.  **Secure Lock for Your Account Key (Password Protected)**
    *   To connect to Discord, the app needs your account's unique "key" (called an Authorization Token). You can save this long key securely under a master password.
    *   For your security, **if you enter the wrong password 3 times in a row**, the saved account key will be completely wiped from your computer.
2.  **Token Masking & Anti-Exposure (Enhanced Security)**
    *   Once input or loaded, your account key (token) is immediately masked as `••••••••••••••••` to prevent accidental exposure or shoulder-surfing. You can temporarily toggle visibility using the view/hide button.
3.  **Clean Any Room You Want**
    *   You can clean a specific text channel in a server, or target a **1-on-1 Direct Message (DM)** room to delete only your past messages.
4.  **Choose Date Ranges**
    *   Easily clean messages based on time, such as "Delete messages from today", "Delete messages from a week ago", or messages sent within a specific date range.
5.  **Delete Specific Messages Only (Filters)**
    *   Delete messages containing specific words.
    *   Delete messages with attached images or files (great for freeing up space).
    *   Delete messages containing links.
6.  **Backup Deleted Messages to PC**
    *   Before deleting messages permanently from Discord, it securely saves and backs up the original content to your local machine (inside the `deleted_backups/` folder) in a text format.
7.  **Chat Log Content Masking (Privacy Guard)**
    *   When enabled, your chat contents are masked as `●●● (Masked)` in the real-time log box and confirmation popup. This protects your private conversations when streaming or taking screenshots, while raw text is still safely written to the local backup files.
8.  **Dynamic SSL Pinning & Ed25519 Verification (Network Security)**
    *   On startup, the client dynamically pulls and updates the latest SSL certificate pins from our remote repository after verifying them with a cryptographic Ed25519 signature. This prevents packet sniffing and Man-in-the-Middle (MITM) attacks, with a safe automatic fallback to default pins if verification or connection fails.

---

## 🚀 Easy 3-Step Guide

### Step 1: Get Your Login Key & Room IDs
Before starting, you need to grab 3 pieces of information so the program knows where to clean.

*   **🔑 Your Account Login Key (Token):**
    1. Log in to Discord using a web browser (like Google Chrome).
    2. Press `F12` on your keyboard to open the Developer Tools.
    3. Click on the **Network** tab at the top.
    4. Type a short message in any chat room or click a channel.
    5. Click on one of the new network requests, look at the headers on the right, find the word `Authorization`, and copy the long string of text next to it.
*   **🏠 Server & Channel IDs:**
    1. Go to Discord Settings -> Advanced -> turn on **Developer Mode**.
    2. Right-click the server icon or the channel name you want to clean, and click **Copy ID** at the bottom.
    *   *※ To clean a 1-on-1 private chat (DM), type **`@me`** in the Server ID box, and paste the DM channel ID in the Channel ID box.*

### Step 2: Run the App & Enter Information
1.  Run the **`UndiscordGUI.exe`** file (which can be generated by double-clicking `build.bat`), or run `python undiscord_gui.py` in your terminal.
2.  Set up your master password to enter the app.
3.  Paste your Login Key (Token), Server ID, and Channel ID into the corresponding boxes.

### Step 3: Start Cleaning
1.  Set any filters (like date ranges or keywords) if needed. If you are not sure, leave them as default.
2.  Click the **[Start]** button at the bottom.
3.  Confirm the prompt, and watch the messages disappear in the real-time log.
4.  If you want to stop during the process, click **[Stop]** to safely halt the cleaner.

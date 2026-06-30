[![Total Downloads](https://img.shields.io/github/downloads/LibraLightLuda/ClearDiscord/total)](https://github.com/LibraLightLuda/ClearDiscord/releases)

# 🧹 디스코드 메시지 청소 대시보드 (Undiscord Python GUI)

이 프로그램은 내가 디스코드 채팅방이나 1:1 대화방(DM)에 썼던 과거의 메시지들을 한 번에 안전하고 깨끗하게 지워주는 편리한 개인용 도구입니다.

---

# 🇰🇷 [한국어 설명] 초보자를 위한 상세 이용 설명서

## 💡 이 프로그램은 무엇인가요?
디스코드에서 수많은 대화를 나누다 보면, 옛날에 내가 쓴 글이나 올린 사진들을 한꺼번에 지우고 싶을 때가 있습니다. 하나하나 마우스로 지우려면 시간이 너무 오래 걸립니다. 
이 프로그램은 **내가 지우고 싶은 방을 지정해서 내가 썼던 글들을 자동으로 빠르게 지워주는 청소기**입니다.

> [!WARNING]
> **⚠️ 꼭 읽어주세요! (주의사항)**
> *   디스코드는 기계(프로그램)를 이용해 글을 대량으로 빠르게 지우는 행위를 공식적으로 권장하지 않습니다.
> *   너무 짧은 시간 동안 많은 글을 연속으로 지우면 계정이 일시 정지되거나 잠길 수 있습니다. 프로그램에서 기본으로 정해주는 안전 대기 시간(1.5초~3초)을 그대로 사용하시는 것을 강력히 권장합니다.

---

## ✨ 대표적인 편리한 기능들
어려운 기술 용어 대신, 누구나 바로 쓸 수 있는 쉬운 기능들이 준비되어 있습니다.

1.  **비밀번호로 로그인 열쇠 잠금 (안전 보관)**
    *   디스코드에 접속하려면 내 계정의 고유한 "로그인 열쇠(토큰)"가 필요합니다. 이 길고 복잡한 열쇠를 매번 입력할 필요가 없도록 비밀번호를 설정해 안전하게 저장해 둡니다.
    *   보안을 위해 **비밀번호를 3번 연속으로 틀리면**, 저장되어 있던 내 계정 열쇠 정보가 컴퓨터에서 완전히 지워집니다.
2.  **원하는 대화방 골라 지우기**
    *   내가 참여 중인 서버의 특정 채팅방만 지울 수도 있고, 친구와의 **1:1 개인 대화방**에 내가 쓴 글만 쏙 골라 지울 수도 있습니다.
3.  **지우고 싶은 날짜 범위 지정하기**
    *   "오늘 쓴 글만 지우기", "1주일 전부터 쓴 글만 지우기", "특정 날짜 사이에 쓴 글만 지우기" 등 날짜를 손쉽게 골라 청소할 수 있습니다.
4.  **특정 글만 골라 지우기 (필터)**
    *   특정 단어가 들어간 글만 지우기
    *   사진이나 동영상 파일이 올라간 글만 지우기 (채널 용량 정리용)
    *   링크 주소가 들어간 글만 지우기

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
> **⚠️ Please Read! (Warnings)**
> *   Discord does not officially support the use of automated tools (self-bots) to delete messages.
> *   Deleting messages too fast can result in temporary or permanent account restrictions. We highly recommend using the default safe delay settings (1.5 to 3 seconds) provided by the app.

---

## ✨ Simple and Useful Features
We have translated complex technical features into easy-to-use functions for everyone.

1.  **Secure Lock for Your Account Key (Password Protected)**
    *   To connect to Discord, the app needs your account's unique "key" (called an Authorization Token). You can save this long key securely under a master password.
    *   For your security, **if you enter the wrong password 3 times in a row**, the saved account key will be completely wiped from your computer.
2.  **Clean Any Room You Want**
    *   You can clean a specific text channel in a server, or target a **1-on-1 Direct Message (DM)** room to delete only your past messages.
3.  **Choose Date Ranges**
    *   Easily clean messages based on time, such as "Delete messages from today", "Delete messages from a week ago", or messages sent within a specific date range.
4.  **Delete Specific Messages Only (Filters)**
    *   Delete messages containing specific words.
    *   Delete messages with attached images or files (great for freeing up space).
    *   Delete messages containing links.

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

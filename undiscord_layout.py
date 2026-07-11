# -*- coding: utf-8 -*-
"""
Undiscord GUI 레이아웃 구성 모듈
Tkinter 위젯 생성, 디스코드 스타일 테마 설정 및 다국어 실시간 UI 번역 전환 기능을 제공합니다.
"""

import webbrowser
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from undiscord_i18n import MESSAGES

def setup_styles(app):
    """프로그램 전반에 적용할 ttk 스타일 및 다크 테마 설정을 정의합니다."""
    app.root.configure(bg=app.bg_dark)
    
    style = ttk.Style()
    style.theme_use('default')
    
    style.configure('TFrame', background=app.bg_dark)
    style.configure('Card.TFrame', background=app.bg_panel)
    style.configure('Bottom.TFrame', background=app.bg_dark)
    
    style.configure('TLabel', background=app.bg_dark, foreground=app.fg_white, font=("Malgun Gothic", 9))
    style.configure('Card.TLabel', background=app.bg_panel, foreground=app.fg_white, font=("Malgun Gothic", 9))
    style.configure('CardBold.TLabel', background=app.bg_panel, foreground=app.fg_white, font=("Malgun Gothic", 9, "bold"))
    
    style.configure('Card.TLabelframe', background=app.bg_panel, borderwidth=1, relief="solid")
    style.configure('Card.TLabelframe.Label', background=app.bg_panel, foreground=app.color_accent, font=("Malgun Gothic", 10, "bold"))

    style.configure('Card.TCheckbutton', background=app.bg_panel, foreground=app.fg_white, font=("Malgun Gothic", 9))
    style.map('Card.TCheckbutton', 
              background=[('active', app.bg_panel)], 
              foreground=[('selected', app.color_success), ('!selected', app.fg_gray), ('active', app.fg_white)])

    style.configure('Success.TButton', background=app.color_success, foreground="#202225", font=("Malgun Gothic", 10, "bold"), borderwidth=0)
    style.map('Success.TButton', background=[('active', '#43b581')])

    style.configure('Danger.TButton', background=app.color_danger, foreground=app.fg_white, font=("Malgun Gothic", 10, "bold"), borderwidth=0)
    style.map('Danger.TButton', background=[('active', '#c93b3e')])
    
    style.configure('Normal.TButton', background="#4f545c", foreground=app.fg_white, font=("Malgun Gothic", 9), borderwidth=0)
    style.map('Normal.TButton', background=[('active', '#686d73')])

    style.configure('Help.TNotebook', background=app.bg_panel, borderwidth=0)
    style.configure('Help.TNotebook.Tab', background="#4f545c", foreground=app.fg_white, font=("Malgun Gothic", 9, "bold"), padding=[10, 4])
    style.map('Help.TNotebook.Tab', background=[('selected', app.color_accent)], foreground=[('selected', app.fg_white)])


def create_widgets(app):
    """2x2 대시보드 레이아웃의 모든 프레임과 인터랙션 위젯을 생성 및 배치합니다."""
    app.root.columnconfigure(0, weight=1)
    app.root.rowconfigure(0, weight=0)
    app.root.rowconfigure(1, weight=1)
    app.root.rowconfigure(2, weight=0)

    # ----------------------------------------------------
    # [상단 영역] 2x2 격자 카드 프레임 설정
    # ----------------------------------------------------
    top_frame = ttk.Frame(app.root, style='TFrame')
    top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
    
    top_frame.columnconfigure(0, weight=1)
    top_frame.columnconfigure(1, weight=1)

    # ---- Card 1: 인증 설정 ----
    app.card1 = ttk.LabelFrame(top_frame, text="  인증 설정  ", style='Card.TLabelframe')
    app.card1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
    app.card1.columnconfigure(0, weight=1)

    # 토큰 입력
    app.lbl_token = ttk.Label(app.card1, text="디스코드 인증 토큰 *", style='CardBold.TLabel')
    app.lbl_token.grid(row=0, column=0, sticky="w", padx=10, pady=(6, 2))
    token_sub = ttk.Frame(app.card1, style='Card.TFrame')
    token_sub.grid(row=1, column=0, sticky="ew", padx=10, pady=2)
    token_sub.columnconfigure(0, weight=1)
    
    app.var_token = tk.StringVar()
    app.entry_token = tk.Entry(token_sub, textvariable=app.var_token, bg=app.bg_input, fg=app.fg_white, insertbackground=app.fg_white, bd=1, relief="flat", show="*")
    app.entry_token.grid(row=0, column=0, sticky="ew", ipady=3)
    app.entry_token.bind("<FocusOut>", app.on_token_focus_out)
    app.entry_token.bind("<Return>", app.on_token_focus_out)
    
    app.btn_toggle_token = ttk.Button(token_sub, text="보기", width=5, style='Normal.TButton', command=app.toggle_token_visibility)
    app.btn_toggle_token.grid(row=0, column=1, padx=(5, 0), sticky="e")
    
    app.btn_easy_login = ttk.Button(token_sub, text="간편 로그인", width=12, style='Normal.TButton', command=app.launch_auto_login)
    app.btn_easy_login.grid(row=0, column=2, padx=(5, 0), sticky="e")

    # 암호화 상태 표시 라벨
    app.lbl_crypto_status = ttk.Label(app.card1, text="", style='Card.TLabel')
    app.lbl_crypto_status.grid(row=2, column=0, sticky="w", padx=10, pady=(4, 2))

    # 작성자 ID
    app.lbl_author = ttk.Label(app.card1, text="작성자 ID (미입력 시 내 계정으로 자동 기입)", style='Card.TLabel')
    app.lbl_author.grid(row=3, column=0, sticky="w", padx=10, pady=(6, 2))
    app.var_author_id = tk.StringVar()
    app.entry_author_id = tk.Entry(app.card1, textvariable=app.var_author_id, bg=app.bg_input, fg=app.fg_white, insertbackground=app.fg_white, bd=1, relief="flat")
    app.entry_author_id.grid(row=4, column=0, sticky="ew", padx=10, pady=(2, 8), ipady=3)

    # ---- Card 2: 삭제 대상 위치 및 범위 ----
    app.card2 = ttk.LabelFrame(top_frame, text="  삭제 대상 위치 및 범위  ", style='Card.TLabelframe')
    app.card2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
    app.card2.columnconfigure(0, weight=1)

    # 서버 ID
    app.lbl_guild = ttk.Label(app.card2, text="서버 ID (DM일 경우 @me 입력) *", style='CardBold.TLabel')
    app.lbl_guild.grid(row=0, column=0, sticky="w", padx=10, pady=(6, 2))
    app.var_guild_id = tk.StringVar()
    app.entry_guild_id = tk.Entry(app.card2, textvariable=app.var_guild_id, bg=app.bg_input, fg=app.fg_white, insertbackground=app.fg_white, bd=1, relief="flat")
    app.entry_guild_id.grid(row=1, column=0, sticky="ew", padx=10, pady=2, ipady=3)

    # 서버 자동 선택 콤보박스 및 로드 버튼
    guild_auto_sub = ttk.Frame(app.card2, style='Card.TFrame')
    guild_auto_sub.grid(row=2, column=0, sticky="ew", padx=10, pady=(2, 6))
    guild_auto_sub.columnconfigure(0, weight=1)
    
    app.combo_guilds = ttk.Combobox(guild_auto_sub, state="readonly", font=("Malgun Gothic", 9))
    app.combo_guilds.grid(row=0, column=0, sticky="ew", padx=(0, 5))
    app.combo_guilds.bind("<<ComboboxSelected>>", app.on_guild_combo_select)
    
    app.btn_load_guilds = ttk.Button(guild_auto_sub, text="서버 불러오기", width=12, style='Normal.TButton', command=app.load_guilds_async)
    app.btn_load_guilds.grid(row=0, column=1, sticky="e")

    # 채널 ID
    app.lbl_channel = ttk.Label(app.card2, text="채널 ID (쉼표[,]로 다중 채널 구분 입력 가능) *", style='CardBold.TLabel')
    app.lbl_channel.grid(row=3, column=0, sticky="w", padx=10, pady=(6, 2))
    app.var_channel_id = tk.StringVar()
    app.entry_channel_id = tk.Entry(app.card2, textvariable=app.var_channel_id, bg=app.bg_input, fg=app.fg_white, insertbackground=app.fg_white, bd=1, relief="flat")
    app.entry_channel_id.grid(row=4, column=0, sticky="ew", padx=10, pady=2, ipady=3)

    # 채널 자동 선택 콤보박스
    channel_auto_sub = ttk.Frame(app.card2, style='Card.TFrame')
    channel_auto_sub.grid(row=5, column=0, sticky="ew", padx=10, pady=(2, 6))
    channel_auto_sub.columnconfigure(0, weight=1)
    
    app.combo_channels = ttk.Combobox(channel_auto_sub, state="readonly", font=("Malgun Gothic", 9))
    app.combo_channels.grid(row=0, column=0, sticky="ew")
    app.combo_channels.bind("<<ComboboxSelected>>", app.on_channel_combo_select)

    # 범위 지정 (최소/최대)
    range_sub = ttk.Frame(app.card2, style='Card.TFrame')
    range_sub.grid(row=6, column=0, sticky="ew", padx=10, pady=(4, 8))
    range_sub.columnconfigure(0, weight=1)
    range_sub.columnconfigure(1, weight=1)

    # 0행: 라벨 배치
    app.lbl_min_range = ttk.Label(range_sub, text="삭제 시작 범위 (이 시각 이후 메시지)", style='Card.TLabel')
    app.lbl_min_range.grid(row=0, column=0, sticky="w", padx=2)
    app.lbl_max_range = ttk.Label(range_sub, text="삭제 종료 범위 (이 시각 이전 메시지)", style='Card.TLabel')
    app.lbl_max_range.grid(row=0, column=1, sticky="w", padx=2)

    # 1행: 입력 텍스트창 배치
    app.var_min_range = tk.StringVar()
    app.entry_min_range = tk.Entry(range_sub, textvariable=app.var_min_range, bg=app.bg_input, fg=app.fg_white, insertbackground=app.fg_white, bd=1, relief="flat")
    app.entry_min_range.grid(row=1, column=0, sticky="ew", padx=2, pady=2, ipady=3)

    app.var_max_range = tk.StringVar()
    app.entry_max_range = tk.Entry(range_sub, textvariable=app.var_max_range, bg=app.bg_input, fg=app.fg_white, insertbackground=app.fg_white, bd=1, relief="flat")
    app.entry_max_range.grid(row=1, column=1, sticky="ew", padx=2, pady=2, ipady=3)

    # 2행: 퀵 설정 라벨 배치
    app.lbl_min_quick = ttk.Label(range_sub, text="└ 삭제 시작시점 자동완성", style='Card.TLabel', foreground=app.fg_gray)
    app.lbl_min_quick.grid(row=2, column=0, sticky="w", padx=2, pady=(2, 0))
    app.lbl_max_quick = ttk.Label(range_sub, text="└ 삭제 종료시점 자동완성", style='Card.TLabel', foreground=app.fg_gray)
    app.lbl_max_quick.grid(row=2, column=1, sticky="w", padx=2, pady=(2, 0))

    # 3행: 콤보박스 배치
    app.combo_min_quick = ttk.Combobox(range_sub, state="readonly", font=("Malgun Gothic", 9))
    app.combo_min_quick.grid(row=3, column=0, sticky="ew", padx=2, pady=2)
    app.combo_min_quick.bind("<<ComboboxSelected>>", app.on_min_quick_select)

    app.combo_max_quick = ttk.Combobox(range_sub, state="readonly", font=("Malgun Gothic", 9))
    app.combo_max_quick.grid(row=3, column=1, sticky="ew", padx=2, pady=2)
    app.combo_max_quick.bind("<<ComboboxSelected>>", app.on_max_quick_select)

    # ---- Card 3: 메시지 상세 필터링 ----
    app.card3 = ttk.LabelFrame(top_frame, text="  메시지 상세 필터링  ", style='Card.TLabelframe')
    app.card3.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
    app.card3.columnconfigure(0, weight=1)

    # 텍스트 검색 필터 (정규표현식 필터 제거됨)
    filter_sub = ttk.Frame(app.card3, style='Card.TFrame')
    filter_sub.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 2))
    filter_sub.columnconfigure(0, weight=1)

    app.lbl_search_text = ttk.Label(filter_sub, text="텍스트 검색어 필터", style='Card.TLabel')
    app.lbl_search_text.grid(row=0, column=0, sticky="w", padx=2)
    app.var_search_text = tk.StringVar()
    app.entry_search_text = tk.Entry(filter_sub, textvariable=app.var_search_text, bg=app.bg_input, fg=app.fg_white, insertbackground=app.fg_white, bd=1, relief="flat")
    app.entry_search_text.grid(row=1, column=0, sticky="ew", padx=2, pady=2, ipady=3)

    # 체크박스 필터 (NSFW 검색 제거, 체크박스 상태 UX 강화를 위해 command 연동)
    chk_sub = ttk.Frame(app.card3, style='Card.TFrame')
    chk_sub.grid(row=1, column=0, sticky="ew", padx=10, pady=(4, 8))
    chk_sub.columnconfigure(0, weight=1)
    chk_sub.columnconfigure(1, weight=1)

    app.update_checkbox_ux = lambda: update_checkbox_ux(app)

    app.var_has_link = tk.BooleanVar(value=False)
    app.chk_has_link = ttk.Checkbutton(chk_sub, text="링크 포함 메시지만 삭제", variable=app.var_has_link, style='Card.TCheckbutton', command=app.update_checkbox_ux)
    app.chk_has_link.grid(row=0, column=0, sticky="w", padx=2, pady=3)

    app.var_has_file = tk.BooleanVar(value=False)
    app.chk_has_file = ttk.Checkbutton(chk_sub, text="파일 첨부 메시지만 삭제", variable=app.var_has_file, style='Card.TCheckbutton', command=app.update_checkbox_ux)
    app.chk_has_file.grid(row=0, column=1, sticky="w", padx=2, pady=3)

    app.var_include_pinned = tk.BooleanVar(value=False)
    app.chk_include_pinned = ttk.Checkbutton(chk_sub, text="핀 고정 메시지도 삭제", variable=app.var_include_pinned, style='Card.TCheckbutton', command=app.update_checkbox_ux)
    app.chk_include_pinned.grid(row=1, column=0, sticky="w", padx=2, pady=3)

    app.var_backup_deleted = tk.BooleanVar(value=False)
    app.chk_backup_deleted = ttk.Checkbutton(chk_sub, text="지운 메시지 PC에 백업", variable=app.var_backup_deleted, style='Card.TCheckbutton', command=app.update_checkbox_ux)
    app.chk_backup_deleted.grid(row=1, column=1, sticky="w", padx=2, pady=3)

    app.var_mask_chat_log = tk.BooleanVar(value=False)
    app.chk_mask_chat_log = ttk.Checkbutton(chk_sub, text="로그에 내 채팅 내용 마스킹", variable=app.var_mask_chat_log, style='Card.TCheckbutton', command=app.update_checkbox_ux)
    app.chk_mask_chat_log.grid(row=2, column=0, columnspan=2, sticky="w", padx=2, pady=3)

    # ---- Card 4: 지연 시간 및 우회 속도 설정 ----
    app.card4 = ttk.LabelFrame(top_frame, text="  지연 시간 및 우회 속도 설정  ", style='Card.TLabelframe')
    app.card4.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
    app.card4.columnconfigure(0, weight=1)

    # 3열 가로 배치 그리드
    delay_grid = ttk.Frame(app.card4, style='Card.TFrame')
    delay_grid.grid(row=0, column=0, sticky="ew", padx=10, pady=(15, 15))
    delay_grid.columnconfigure(0, weight=1)
    delay_grid.columnconfigure(1, weight=1)
    delay_grid.columnconfigure(2, weight=1)

    # 검색 지연
    app.lbl_search_delay = ttk.Label(delay_grid, text="검색 대기 시간 (밀리초)", style='Card.TLabel')
    app.lbl_search_delay.grid(row=0, column=0, sticky="w", padx=2)
    app.var_search_delay = tk.IntVar(value=100)
    app.entry_search_delay = tk.Entry(delay_grid, textvariable=app.var_search_delay, bg=app.bg_input, fg=app.fg_white, insertbackground=app.fg_white, bd=1, relief="flat")
    app.entry_search_delay.grid(row=1, column=0, sticky="ew", padx=2, pady=2, ipady=3)

    # 최소 랜덤 지연
    app.lbl_min_delay = ttk.Label(delay_grid, text="최소 삭제 대기 (밀리초)", style='Card.TLabel')
    app.lbl_min_delay.grid(row=0, column=1, sticky="w", padx=2)
    app.var_min_delay = tk.IntVar(value=1500)
    app.entry_min_delay = tk.Entry(delay_grid, textvariable=app.var_min_delay, bg=app.bg_input, fg=app.fg_white, insertbackground=app.fg_white, bd=1, relief="flat")
    app.entry_min_delay.grid(row=1, column=1, sticky="ew", padx=2, pady=2, ipady=3)

    # 최대 랜덤 지연 (기본 권장 최대 삭제 대기 시간을 3000ms에서 5000ms로 변경)
    app.lbl_max_delay = ttk.Label(delay_grid, text="최대 삭제 대기 (밀리초)", style='Card.TLabel')
    app.lbl_max_delay.grid(row=0, column=2, sticky="w", padx=2)
    app.var_max_delay = tk.IntVar(value=5000)
    app.entry_max_delay = tk.Entry(delay_grid, textvariable=app.var_max_delay, bg=app.bg_input, fg=app.fg_white, insertbackground=app.fg_white, bd=1, relief="flat")
    app.entry_max_delay.grid(row=1, column=2, sticky="ew", padx=2, pady=2, ipady=3)

    # ----------------------------------------------------
    # [하단 영역] 진행 바, 제어 버튼, 로그 터미널 창
    # ----------------------------------------------------
    bottom_frame = ttk.Frame(app.root, style='TFrame')
    bottom_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(5, 15))
    
    bottom_frame.columnconfigure(0, weight=3, minsize=250)
    bottom_frame.columnconfigure(1, weight=7, minsize=500)
    bottom_frame.rowconfigure(0, weight=1)

    # ---- 하단 좌측: 제어 패널 ----
    ctrl_panel = ttk.Frame(bottom_frame, style='TFrame')
    ctrl_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
    ctrl_panel.columnconfigure(0, weight=1)
    ctrl_panel.rowconfigure(5, weight=1)

    # 상단 로고 프레임 (한/영 전환 버튼 병렬 배치)
    logo_sub = ttk.Frame(ctrl_panel, style='TFrame')
    logo_sub.grid(row=0, column=0, sticky="ew", pady=(5, 0))
    logo_sub.columnconfigure(0, weight=1)
    
    logo_label = tk.Label(logo_sub, text="UNDISCORD", font=("Segoe UI", 22, "bold"), fg=app.color_accent, bg=app.bg_dark)
    logo_label.grid(row=0, column=0, sticky="w")
    
    # 🌐 다국어 한글/영어 전환 토글 버튼 배치
    app.btn_lang_toggle = ttk.Button(logo_sub, text="🌐 English / 한국어", style='Normal.TButton', command=app.toggle_language)
    app.btn_lang_toggle.grid(row=0, column=1, sticky="e", padx=(10, 0))

    # 앱 정보 서브 텍스트
    app.info_sub = ttk.Frame(ctrl_panel, style='TFrame')
    app.info_sub.grid(row=1, column=0, sticky="w", pady=(0, 15))
    
    app.lbl_desc = tk.Label(
        app.info_sub, 
        text="디스코드 메시지 일괄 삭제 도구 (파이썬 V1.0)", 
        font=("Malgun Gothic", 9), 
        fg=app.fg_gray, 
        bg=app.bg_dark, 
        justify="left"
    )
    app.lbl_desc.grid(row=0, column=0, columnspan=4, sticky="w")
    
    # 만든이 LibraLight
    app.lbl_creator_title = tk.Label(app.info_sub, text="만든이: ", font=("Malgun Gothic", 8), fg=app.fg_gray, bg=app.bg_dark)
    app.lbl_creator_title.grid(row=1, column=0, sticky="w", pady=(2, 0))
    
    lbl_creator_link = tk.Label(
        app.info_sub, 
        text="LibraLight", 
        font=("Malgun Gothic", 8, "bold", "underline"), 
        fg=app.color_success, 
        bg=app.bg_dark, 
        cursor="hand2"
    )
    lbl_creator_link.grid(row=1, column=1, sticky="w", pady=(2, 0))
    # 만든이 링크를 디스코드 채널 대신 깃허브 저장소 주소로 연결하도록 변경
    lbl_creator_link.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://github.com/LibraLightLuda/ClearDiscord"))
    
    # 원본 GitHub 링크
    app.lbl_source_title = tk.Label(app.info_sub, text="  |  오픈소스: ", font=("Malgun Gothic", 8), fg=app.fg_gray, bg=app.bg_dark)
    app.lbl_source_title.grid(row=1, column=2, sticky="w", pady=(2, 0))
    
    lbl_repo_link = tk.Label(
        app.info_sub, 
        text="victornpb/undiscord", 
        font=("Malgun Gothic", 8, "underline"), 
        fg=app.color_accent, 
        bg=app.bg_dark, 
        cursor="hand2"
    )
    lbl_repo_link.grid(row=1, column=3, sticky="w", pady=(2, 0))
    lbl_repo_link.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://github.com/victornpb/undiscord"))

    app.btn_start = ttk.Button(ctrl_panel, text="작업 시작", style='Success.TButton', command=app.click_start)
    app.btn_start.grid(row=2, column=0, sticky="ew", ipady=6, pady=4)

    app.btn_stop = ttk.Button(ctrl_panel, text="작업 중단", style='Danger.TButton', command=app.click_stop, state="disabled")
    app.btn_stop.grid(row=3, column=0, sticky="ew", ipady=6, pady=4)

    app.btn_clear = ttk.Button(ctrl_panel, text="로그 창 비우기", style='Normal.TButton', command=app.click_clear_log)
    app.btn_clear.grid(row=4, column=0, sticky="ew", ipady=6, pady=4)

    app.btn_help = ttk.Button(ctrl_panel, text="이용 도움말 (인증키 및 ID 획득법)", style='Normal.TButton', command=app.show_help_window)
    app.btn_help.grid(row=5, column=0, sticky="ew", ipady=6, pady=(15, 4))

    # ---- 하단 우측: 진행 상태 및 로그 창 ----
    log_panel = ttk.Frame(bottom_frame, style='TFrame')
    log_panel.grid(row=0, column=1, sticky="nsew", pady=5)
    log_panel.columnconfigure(0, weight=1)
    log_panel.rowconfigure(2, weight=1)

    app.var_progress_status = tk.StringVar()
    app.lbl_status = ttk.Label(log_panel, textvariable=app.var_progress_status, style='TLabel')
    app.lbl_status.grid(row=0, column=0, sticky="w", pady=(0, 3))

    app.progress_bar = ttk.Progressbar(log_panel, orient="horizontal", mode="determinate")
    app.progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))

    app.log_area = ScrolledText(log_panel, bg="#2f3136", fg=app.fg_white, insertbackground=app.fg_white, font=("Consolas", 9), bd=0, wrap="word")
    app.log_area.grid(row=2, column=0, sticky="nsew")
    
    app.log_area.tag_config('success', foreground=app.color_success)
    app.log_area.tag_config('warn', foreground="#faa61a")
    app.log_area.tag_config('error', foreground=app.color_danger)
    app.log_area.tag_config('info', foreground="#7289da")
    app.log_area.tag_config('verb', foreground="#72767d")
    app.log_area.tag_config('debug', foreground=app.fg_white)

    # 텍스트 초기화 구동
    update_ui_texts(app)


def update_ui_texts(app):
    """현재 언어 설정(app.current_lang)에 따라 UI의 모든 텍스트 컴포넌트를 동적으로 로드 및 번역합니다."""
    lang = app.current_lang
    msg = MESSAGES[lang]
    
    # 윈도우 타이틀
    app.root.title(msg['title'])
    
    # 각 카드 제목
    app.card1.configure(text=msg['card_auth_title'])
    app.card2.configure(text=msg['card_target_title'])
    app.card3.configure(text=msg['card_filter_title'])
    app.card4.configure(text=msg['card_delay_title'])
    
    # 카드 1: 인증 설정
    app.lbl_token.configure(text=msg['token_label'])
    app.lbl_author.configure(text=msg['author_id_label'])
    
    # 암호화 상태 라벨 업데이트
    if getattr(app, 'session_password', None) == "":
        app.lbl_crypto_status.configure(text=msg['status_plaintext'], foreground=app.color_danger)
    elif getattr(app, 'session_password', None):
        app.lbl_crypto_status.configure(text=msg['status_encrypted'], foreground=app.color_success)
    else:
        app.lbl_crypto_status.configure(text="", foreground=app.fg_white)
    
    # 토큰 보기/숨기기 버튼 상태 동기화
    if app.entry_token.cget("show") == "*":
        app.btn_toggle_token.configure(text=msg['btn_view'])
    else:
        app.btn_toggle_token.configure(text=msg['btn_hide'])
        
    app.btn_easy_login.configure(text=msg['btn_easy_login'])
        
    # 카드 2: 위치 및 범위
    app.lbl_guild.configure(text=msg['guild_id_label'])
    app.lbl_channel.configure(text=msg['channel_id_label'])
    app.lbl_min_range.configure(text=msg['min_range_label'])
    app.lbl_max_range.configure(text=msg['max_range_label'])
    app.lbl_min_quick.configure(text=msg['min_quick_lbl'])
    app.lbl_max_quick.configure(text=msg['max_quick_lbl'])
    
    # 신규 자동 선택 콤보박스 및 버튼 텍스트
    app.btn_load_guilds.configure(text=msg['btn_load_guilds'])
    
    prev_g_val = app.combo_guilds.get()
    placeholders_g = [MESSAGES['ko']['combo_guild_placeholder'], MESSAGES['en']['combo_guild_placeholder']]
    if not prev_g_val or prev_g_val in placeholders_g:
        app.combo_guilds.configure(values=[msg['combo_guild_placeholder']])
        app.combo_guilds.set(msg['combo_guild_placeholder'])
        
    prev_c_val = app.combo_channels.get()
    placeholders_c = [MESSAGES['ko']['combo_channel_placeholder'], MESSAGES['en']['combo_channel_placeholder']]
    if not prev_c_val or prev_c_val in placeholders_c:
        app.combo_channels.configure(values=[msg['combo_channel_placeholder']])
        app.combo_channels.set(msg['combo_channel_placeholder'])
    
    # 카드 2 콤보박스 텍스트 리로드 (선택 인덱스 보존)
    min_idx = app.combo_min_quick.current()
    max_idx = app.combo_max_quick.current()
    
    app.combo_min_quick.configure(values=msg['quick_options'])
    app.combo_max_quick.configure(values=msg['quick_options'])
    
    # 인덱스 유효할 경우 복원, 아니면 0
    app.combo_min_quick.current(min_idx if min_idx >= 0 else 0)
    app.combo_max_quick.current(max_idx if max_idx >= 0 else 0)
    
    # 카드 3: 상세 필터링
    app.lbl_search_text.configure(text=msg['search_text_label'])
    update_checkbox_ux(app)
    
    # 카드 4: 지연 대기 설정
    app.lbl_search_delay.configure(text=msg['search_delay_label'])
    app.lbl_min_delay.configure(text=msg['min_delay_label'])
    app.lbl_max_delay.configure(text=msg['max_delay_label'])
    
    # 하단 좌측 컨트롤 패널
    app.lbl_desc.configure(text=msg['app_desc'])
    app.lbl_creator_title.configure(text=msg['made_by'])
    app.lbl_source_title.configure(text=msg['open_source'])
    
    app.btn_start.configure(text=msg['btn_start'])
    app.btn_stop.configure(text=msg['btn_stop'])
    app.btn_clear.configure(text=msg['btn_clear'])
    app.btn_help.configure(text=msg['btn_help'])
    
    # 현재 엔진 상태가 정지 중일 때만 기본 대기 메시지 번역 로드
    if not app.engine or not app.engine.state['running']:
        app.var_progress_status.set(msg['progress_wait'])
    
    # 토글 버튼 텍스트 변경
    next_lang_name = "한국어" if lang == 'en' else "English"
    app.btn_lang_toggle.configure(text=f"🌐 {next_lang_name}")


def update_checkbox_ux(app):
    """체크박스의 체크 여부에 따라 [활성] / [비활성] 접두사를 붙여 시각적으로 상태를 인지하기 쉽게 합니다."""
    try:
        msg = MESSAGES[app.current_lang]
        status_active = msg.get('status_active', "[활성] ")
        status_inactive = msg.get('status_inactive', "[비활성] ")
        
        # 1. 링크 포함 메시지
        has_link_text = f"{status_active if app.var_has_link.get() else status_inactive}{msg.get('chk_has_link', '링크 포함 메시지만 삭제')}"
        app.chk_has_link.configure(text=has_link_text)
        
        # 2. 파일 첨부 메시지
        has_file_text = f"{status_active if app.var_has_file.get() else status_inactive}{msg.get('chk_has_file', '파일 첨부 메시지만 삭제')}"
        app.chk_has_file.configure(text=has_file_text)
        
        # 3. 핀 고정 메시지
        include_pinned_text = f"{status_active if app.var_include_pinned.get() else status_inactive}{msg.get('chk_include_pinned', '핀 고정 메시지도 삭제')}"
        app.chk_include_pinned.configure(text=include_pinned_text)
        
        # 4. 지운 메시지 백업
        backup_deleted_text = f"{status_active if app.var_backup_deleted.get() else status_inactive}{msg.get('chk_backup_deleted', '지운 메시지 PC에 백업')}"
        app.chk_backup_deleted.configure(text=backup_deleted_text)
        
        # 5. 로그 내 채팅 내용 마스킹
        mask_chat_log_text = f"{status_active if app.var_mask_chat_log.get() else status_inactive}{msg.get('chk_mask_chat_log', '로그에 내 채팅 내용 마스킹')}"
        app.chk_mask_chat_log.configure(text=mask_chat_log_text)
        
        # 마스킹 여부가 실제로 변경되었을 때만 로그창을 갱신합니다.
        current_mask_val = app.var_mask_chat_log.get()
        if not hasattr(app, '_last_mask_chat_log_val') or app._last_mask_chat_log_val != current_mask_val:
            app._last_mask_chat_log_val = current_mask_val
            if app.engine:
                app.engine.options['maskChatLog'] = current_mask_val
            if hasattr(app, 'log_history') and hasattr(app, 'redraw_logs'):
                app.redraw_logs()
    except Exception as e:
        print(f"체크박스 UX 업데이트 에러: {e}")

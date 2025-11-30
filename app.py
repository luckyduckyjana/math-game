import streamlit as st
import streamlit.components.v1 as components
import random
import time
import base64
import os
import csv
import pandas as pd
from datetime import datetime

# --- 1. 기본 설정 및 파일 로드 ---
st.set_page_config(page_title="럭키덕키 스피드 구구단", page_icon="🐣", layout="centered")

IMG_DIR = "images"
RANK_DIR = "rank"
RANK_FILE = os.path.join(RANK_DIR, "ranking_speed.csv")

if not os.path.exists(RANK_DIR): os.makedirs(RANK_DIR)
if not os.path.exists(RANK_FILE):
    with open(RANK_FILE, mode='w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(["이름", "단", "기록(초)", "날짜"])

# [유지] 캐싱 기능 활성화 (이미지 로딩 속도 최적화)
@st.cache_data
def load_image_as_base64(filename_no_ext):
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join(IMG_DIR, filename_no_ext + ext)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = f.read()
                encoded = base64.b64encode(data).decode()
                mime = "image/png" if ext == ".png" else "image/jpeg"
                return f"data:{mime};base64,{encoded}"
    return None

mole_b64 = load_image_as_base64("mole")
hole_b64 = load_image_as_base64("hole")
clock_b64 = load_image_as_base64("duck_clock")

images_ready = (mole_b64 and hole_b64 and clock_b64)

# --- 2. CSS 스타일 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #8D6E63; }}
    
    .title-box {{
        text-align: center; color: #FFD54F; font-size: 2.5em; 
        text-shadow: 3px 3px 0px #3E2723; margin-bottom: 20px;
        font-family: 'Comic Sans MS', sans-serif;
    }}

    .number-label {{
        text-align: center; font-size: 28px; font-weight: bold;
        color: white; text-shadow: 2px 2px 4px black;
        margin-top: -20px; pointer-events: none;
        position: relative; z-index: 100;
    }}

    .question-box {{
        text-align: center; font-size: 45px; font-weight: bold;
        background: #FFECB3; border: 4px solid #FFC107; 
        border-radius: 15px; margin: 15px 0; color: #3E2723;
        padding: 10px;
    }}

    .feedback-box {{
        font-size: 24px; font-weight: bold; padding: 10px;
        border-radius: 10px; background-color: rgba(255, 255, 255, 0.9);
        text-align: center; animation: fadeIn 0.3s;
        border: 2px solid #3E2723;
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(-10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. JavaScript 타이머 ---
def render_js_timer(server_elapsed_time, penalty_time, background_img):
    timer_html = f"""
    <style>
        .js-clock-container {{
            position: relative;
            width: 160px; height: 160px;
            margin: 0 auto;
            background-color: transparent;
            background-image: url("{background_img}");
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            display: flex; justify-content: center; align-items: center;
        }}
        .js-clock-text {{
            font-size: 38px; font-weight: bold; color: #333;
            margin-top: 0px; 
            padding-bottom: 15px;
            text-shadow: 1px 1px 0px white;
            font-family: sans-serif;
            white-space: nowrap;
        }}
    </style>
    <div class="js-clock-container">
        <div id="timer-display" class="js-clock-text">0.0</div>
    </div>
    <script>
        const initialElapsed = {server_elapsed_time};
        const penalty = {penalty_time};
        const localStartTime = new Date().getTime() / 1000 - initialElapsed;

        function updateTimer() {{
            const now = new Date().getTime() / 1000;
            const totalElapsed = Math.max(0, now - localStartTime + penalty);
            const display = document.getElementById("timer-display");
            if(display) {{ display.innerText = totalElapsed.toFixed(1); }}
        }}
        setInterval(updateTimer, 50);
    </script>
    """
    components.html(timer_html, height=170)

# --- 4. 게임 로직 ---

TARGET_COUNT = 9

# [수정됨] 기록 저장 로직: 기존 기록 확인 후 갱신
def save_record(name, dan, record_time):
    rows = []
    updated = False
    
    # 기존 파일 읽기
    if os.path.exists(RANK_FILE):
        with open(RANK_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                rows.append(header)
                for row in reader:
                    # row = [이름, 단, 기록, 날짜]
                    if len(row) < 4: continue # 데이터 깨짐 방지
                    
                    saved_name = row[0]
                    saved_dan = row[1]
                    saved_time = float(row[2])
                    
                    # 같은 이름, 같은 단인 경우
                    if saved_name == name and saved_dan == f"{dan}단":
                        if record_time < saved_time: # 신기록이면 갱신
                            row[2] = f"{record_time:.2f}"
                            row[3] = datetime.now().strftime("%Y-%m-%d")
                            updated = True
                        else:
                            # 기존 기록이 더 좋으면 유지하되, 업데이트 처리된 것으로 간주
                            updated = True
                    rows.append(row)
    
    # 새로운 도전(리스트에 없던 경우)이라면 추가
    if not updated:
        date_str = datetime.now().strftime("%Y-%m-%d")
        rows.append([name, f"{dan}단", f"{record_time:.2f}", date_str])
    
    # 파일에 다시 쓰기
    with open(RANK_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def load_ranking(dan_filter="전체"):
    try:
        df = pd.read_csv(RANK_FILE)
        df["기록(초)"] = pd.to_numeric(df["기록(초)"], errors='coerce')
        if dan_filter != "전체":
            df = df[df["단"] == dan_filter]
        df = df.sort_values(by="기록(초)", ascending=True).head(5)
        df.index = range(1, len(df) + 1)
        df["기록(초)"] = df["기록(초)"].apply(lambda x: f"{x:.2f}초")
        return df[["이름", "단", "기록(초)", "날짜"]]
    except: return pd.DataFrame()

def generate_new_problem(dan):
    if 'problem_deck' not in st.session_state or not st.session_state.problem_deck:
        st.session_state.problem_deck = list(range(1, 10))
        random.shuffle(st.session_state.problem_deck)
    
    multiplier = st.session_state.problem_deck.pop(0)
    answer = dan * multiplier
    
    grid_numbers = [answer]
    while len(grid_numbers) < 9:
        wrong = random.randint(1, 81)
        if wrong != answer and wrong not in grid_numbers:
            grid_numbers.append(wrong)
    random.shuffle(grid_numbers)
    
    answer_idx = grid_numbers.index(answer)
    indices = list(range(9))
    indices.remove(answer_idx)
    wrong_mole_idx = random.choice(indices)
    
    return {
        'problem': f"{dan} x {multiplier}",
        'answer': answer,
        'grid': grid_numbers,
        'correct_mole_idx': answer_idx,
        'wrong_mole_idx': wrong_mole_idx
    }

def check_answer(idx):
    current = st.session_state.game_state
    if current is None: return

    # 알림 메시지 업데이트
    if idx == current['correct_mole_idx']:
        st.session_state.caught_count += 1
        st.session_state.feedback_msg = f"🟢 잡았다!<br>({st.session_state.caught_count}/{TARGET_COUNT})"
        st.session_state.feedback_color = "#E8F5E9" 
        
        if st.session_state.caught_count >= TARGET_COUNT:
            finish_game()
        else:
            st.session_state.game_state = generate_new_problem(st.session_state.setting_dan)
            
    elif idx == current['wrong_mole_idx']:
        st.session_state.feedback_msg = "💥 함정!<br>+3초"
        st.session_state.feedback_color = "#FFEBEE" 
        st.session_state.penalty_time += 3.0 
    else:
        st.session_state.feedback_msg = "❌ 빈 땅!<br>+1초"
        st.session_state.feedback_color = "#FFF3E0" 
        st.session_state.penalty_time += 1.0

def finish_game():
    end_time = time.time()
    start = st.session_state.get('start_time', end_time)
    final_record = (end_time - start) + st.session_state.penalty_time
    st.session_state.final_record = final_record
    save_record(st.session_state.user_name, st.session_state.setting_dan, final_record)
    st.session_state.page = 'clear'

# --- 5. 페이지 이동 함수들 ---
def toggle_help():
    st.session_state.show_help = not st.session_state.get('show_help', False)

def go_to_setup(): 
    st.session_state.page = 'setup'

def go_to_game():
    if st.session_state.temp_name.strip() == "":
        st.warning("이름을 입력해주세요!")
        return
    st.session_state.user_name = st.session_state.temp_name
    st.session_state.setting_dan = st.session_state.temp_dan
    st.session_state.caught_count = 0
    st.session_state.penalty_time = 0.0
    st.session_state.game_state = None
    
    st.session_state.feedback_msg = "시작!"
    st.session_state.feedback_color = "#FFFFFF"
    
    deck = list(range(1, 10))
    random.shuffle(deck)
    st.session_state.problem_deck = deck
    
    st.session_state.page = 'playing'

def go_home(): 
    st.session_state.page = 'intro'

# --- 6. 메인 UI ---
if 'page' not in st.session_state: st.session_state.page = 'intro'
if 'show_help' not in st.session_state: st.session_state.show_help = False
if 'feedback_msg' not in st.session_state: st.session_state.feedback_msg = ""
if 'feedback_color' not in st.session_state: st.session_state.feedback_color = "#FFFFFF"

if not images_ready:
    st.error("⚠️ 이미지 로드 실패! images 폴더 확인 필요.")
    st.stop()

# [PAGE 1] 인트로
if st.session_state.page == 'intro':
    st.markdown("<div class='title-box'>🐣 럭키덕키 타임어택 🐣</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            st.button("⏱️ 도전 시작", on_click=go_to_setup, use_container_width=True, type="primary")
        with btn_c2:
            st.button("❓ 게임 방법", on_click=toggle_help, use_container_width=True)
        
        if st.session_state.show_help:
            with st.container(border=True):
                st.markdown("""
                ### 🐹 게임 규칙 설명
                **1. 스피드 타임어택!** ⏱️
                * 선택한 구구단의 **x1 ~ x9 (총 9문제)**가 무작위로 나옵니다.
                * 모든 문제를 **가장 짧은 시간** 안에 푸는 것이 목표!
                
                **2. 조작 방법** 🎮
                * 정답 두더지를 **마우스로 클릭**하거나 **화면을 터치**하세요.
                
                **3. 주의하세요! (페널티)** 💥
                * **함정 두더지**를 잡으면 **+3초**
                * **빈 땅**을 파면 **+1초**
                """)
                if st.button("❌ 닫기", use_container_width=True):
                    toggle_help()
                    st.rerun()

        st.write("---")
        st.markdown("<h4 style='text-align:center; color:white;'>🏆 명예의 전당</h4>", unsafe_allow_html=True)
        
        filter_options = ["전체"] + [f"{i}단" for i in range(2, 10)]
        selected_filter = st.selectbox("랭킹 보기", filter_options)
        ranking = load_ranking(selected_filter)
        
        if not ranking.empty:
            st.dataframe(ranking, use_container_width=True, hide_index=False)
        else:
            st.info(f"아직 {selected_filter} 기록이 없습니다.")

# [PAGE 2] 설정
elif st.session_state.page == 'setup':
    st.button("🏠 처음으로", on_click=go_home)
    
    st.markdown("<div class='title-box'>⚙️ 도전 준비</div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.text_input("도전자 이름", key="temp_name", placeholder="이름을 입력하세요")
        st.selectbox("구구단 선택", range(2, 10), key="temp_dan")
        st.info(f"💡 {st.session_state.get('temp_dan', 2)}단의 1부터 9까지 곱셈이 랜덤하게 나옵니다! (총 {TARGET_COUNT}문제)")
        st.button("🔥 게임 스타트!", on_click=go_to_game, use_container_width=True, type="primary")

# [PAGE 3] 게임 플레이
elif st.session_state.page == 'playing':
    if st.session_state.game_state is None:
        st.session_state.game_state = generate_new_problem(st.session_state.setting_dan)
        st.session_state.start_time = time.time()
    
    game = st.session_state.game_state
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: st.markdown(f"**👤 {st.session_state.user_name}** ({st.session_state.setting_dan}단)")
    with c2: st.markdown(f"🎯 목표: **{st.session_state.caught_count} / {TARGET_COUNT}**")
    
    with c3:
        st.button("❌ 포기하기", on_click=go_home, use_container_width=True)

    t1, t2, t3 = st.columns([1, 2, 1])
    
    with t2:
        current_server_time = time.time()
        elapsed_server = current_server_time - st.session_state.start_time
        render_js_timer(elapsed_server, st.session_state.penalty_time, clock_b64)
    
    with t3:
        st.write("") 
        st.write("")
        if st.session_state.feedback_msg:
            st.markdown(f"""
            <div class='feedback-box' style='background-color:{st.session_state.feedback_color};'>
                {st.session_state.feedback_msg}
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"<div class='question-box'>{game['problem']} = ?</div>", unsafe_allow_html=True)

    for row in range(3):
        cols = st.columns(3)
        for col in range(3):
            idx = row * 3 + col
            
            is_correct = (idx == game['correct_mole_idx'])
            is_wrong = (idx == game['wrong_mole_idx'])
            bg_url = mole_b64 if (is_correct or is_wrong) else hole_b64
            
            number = game['grid'][idx]
            btn_key = f"btn_{idx}"

            st.markdown(f"""
            <style>
            .st-key-{btn_key} button {{
                background-image: url("{bg_url}") !important;
                background-size: contain !important;
                background-repeat: no-repeat !important;
                background-position: center center !important;
                background-color: transparent !important;
                border: none !important;
                height: 100px !important;
                width: 100% !important;
            }}
            .st-key-{btn_key} button:hover {{ background-color: rgba(0,0,0,0.1) !important; }}
            </style>
            """, unsafe_allow_html=True)
            
            with cols[col]:
                st.button(" ", key=btn_key, on_click=check_answer, args=(idx,), use_container_width=True)
                st.markdown(f"<div class='number-label'>{number}</div>", unsafe_allow_html=True)

# [PAGE 4] 클리어
elif st.session_state.page == 'clear':
    st.balloons()
    st.markdown("<div class='title-box'>🎉 축하합니다! 🎉</div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f"""
        <div style='text-align:center; font-size:24px;'>
            <b>{st.session_state.user_name}</b>님의 기록<br>
            <span style='font-size:48px; color:#E91E63; font-weight:bold;'>{st.session_state.final_record:.2f}초</span>
        </div>
        """, unsafe_allow_html=True)
        
        # [수정] 다시 도전 버튼 삭제, 홈으로 버튼만 유지
        st.button("🏠 홈으로 이동", on_click=go_home, use_container_width=True, type="primary")
import streamlit as st
import random
import time
import base64
import os
import csv
import pandas as pd
from datetime import datetime

# --- 1. 기본 설정 및 파일 로드 ---
st.set_page_config(page_title="럭키덕키 구구단", page_icon="🐹", layout="centered")

IMG_DIR = "images"
RANK_DIR = "rank"
RANK_FILE = os.path.join(RANK_DIR, "ranking_speed.csv")

# 폴더/파일 생성 (없으면 자동 생성)
if not os.path.exists(RANK_DIR): os.makedirs(RANK_DIR)
if not os.path.exists(RANK_FILE):
    with open(RANK_FILE, mode='w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(["이름", "기록(초)", "날짜"])

# 이미지 파일 자동 찾기 및 Base64 변환 함수 (확장자 걱정 NO)
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

# 이미지 로드
mole_b64 = load_image_as_base64("mole")
hole_b64 = load_image_as_base64("hole")
clock_b64 = load_image_as_base64("duck_clock")

images_ready = (mole_b64 and hole_b64 and clock_b64)

# --- 2. CSS 스타일 (버튼 디자인 수정) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #8D6E63; }}
    
    /* 타이틀 */
    .title-box {{
        text-align: center; color: #FFD54F; font-size: 2.5em; 
        text-shadow: 3px 3px 0px #3E2723; margin-bottom: 20px;
        font-family: 'Comic Sans MS', sans-serif;
    }}

    /* 오리 시계 */
    .clock-container {{
        position: relative;
        width: 160px; height: 160px;
        margin: 0 auto;
        background-image: url("{clock_b64}");
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        display: flex; justify-content: center; align-items: center;
    }}
    .clock-text {{
        font-size: 36px; font-weight: bold; color: #333;
        padding-top: 35px; text-shadow: 1px 1px 0px white;
    }}

    /* 버튼 아래 숫자 스타일 */
    .number-label {{
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        color: white;
        text-shadow: 2px 2px 4px black;
        margin-top: -15px; /* 버튼과 숫자 사이 간격 */
        pointer-events: none; /* 숫자가 클릭 방해하지 않게 */
    }}

    /* 문제 박스 */
    .question-box {{
        text-align: center; font-size: 45px; font-weight: bold;
        background: #FFECB3; border: 4px solid #FFC107; 
        border-radius: 15px; margin: 15px 0; color: #3E2723;
        padding: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. 게임 로직 ---

TARGET_COUNT = 10 

def save_record(name, record_time):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(RANK_FILE, mode='a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([name, f"{record_time:.2f}", date_str])

def load_ranking():
    try:
        df = pd.read_csv(RANK_FILE)
        df = df.sort_values(by="기록(초)", ascending=True).head(5)
        df.index = range(1, len(df) + 1)
        df["기록(초)"] = df["기록(초)"].apply(lambda x: f"{x}초")
        return df
    except: return pd.DataFrame()

def generate_new_problem(dan):
    multiplier = random.randint(1, 9)
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

# ★ 핵심 수정: 콜백 함수로 변경 (버튼 누르면 즉시 실행됨) ★
def check_answer(idx):
    current = st.session_state.game_state
    if current is None: return

    # 정답 체크
    if idx == current['correct_mole_idx']:
        st.session_state.caught_count += 1
        st.toast(f"잡았다! ({st.session_state.caught_count}/{TARGET_COUNT})", icon="🐹")
        
        if st.session_state.caught_count >= TARGET_COUNT:
            finish_game()
        else:
            st.session_state.game_state = generate_new_problem(st.session_state.setting_dan)
            
    elif idx == current['wrong_mole_idx']:
        st.toast("함정! (+3초 페널티)", icon="💥")
        st.session_state.penalty_time += 3.0 
    else:
        st.toast("빈 땅입니다. (+1초 페널티)", icon="❌")
        st.session_state.penalty_time += 1.0

def process_input():
    user_input = st.session_state.kbd_input
    if user_input:
        key_map = {'7':0, '8':1, '9':2, '4':3, '5':4, '6':5, '1':6, '2':7, '3':8}
        if user_input[-1] in key_map:
            check_answer(key_map[user_input[-1]])
        st.session_state.kbd_input = ""

def finish_game():
    end_time = time.time()
    final_record = (end_time - st.session_state.start_time) + st.session_state.penalty_time
    st.session_state.final_record = final_record
    save_record(st.session_state.user_name, final_record)
    st.session_state.page = 'clear'

# --- 4. 페이지 이동 ---
def go_to_setup(): st.session_state.page = 'setup'
def go_to_game():
    if st.session_state.temp_name.strip() == "":
        st.warning("이름을 입력해주세요!")
        return
    st.session_state.user_name = st.session_state.temp_name
    st.session_state.setting_dan = st.session_state.temp_dan
    st.session_state.caught_count = 0
    st.session_state.penalty_time = 0.0
    st.session_state.start_time = time.time()
    st.session_state.game_state = None
    st.session_state.page = 'playing'

def go_home(): st.session_state.page = 'intro'

# --- 5. 메인 UI ---
if 'page' not in st.session_state: st.session_state.page = 'intro'

if not images_ready:
    st.error("⚠️ 이미지 로드 실패! images 폴더에 mole, hole, duck_clock 이미지가 있는지 확인하세요.")
    st.stop()

# [PAGE 1] 인트로
if st.session_state.page == 'intro':
    st.markdown("<div class='title-box'>🐹 럭키덕키 타임어택 🐹</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button("⏱️ 도전 시작하기", on_click=go_to_setup, use_container_width=True, type="primary")
        st.write("---")
        st.markdown("<h4 style='text-align:center; color:white;'>🏆 명예의 전당 (Fastest)</h4>", unsafe_allow_html=True)
        ranking = load_ranking()
        if not ranking.empty:
            st.dataframe(ranking[["이름", "기록(초)"]], use_container_width=True, hide_index=False)
        else:
            st.info("아직 기록이 없습니다.")

# [PAGE 2] 설정
elif st.session_state.page == 'setup':
    st.markdown("<div class='title-box'>⚙️ 도전 준비</div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.text_input("도전자 이름", key="temp_name", placeholder="이름을 입력하세요")
        st.selectbox("구구단 선택", range(2, 10), key="temp_dan")
        st.info(f"💡 정답 두더지 **{TARGET_COUNT}마리**를 빠르게 잡으세요!")
        st.button("🔥 게임 스타트!", on_click=go_to_game, use_container_width=True, type="primary")

# [PAGE 3] 게임 플레이
elif st.session_state.page == 'playing':
    if st.session_state.game_state is None:
        st.session_state.game_state = generate_new_problem(st.session_state.setting_dan)
    
    game = st.session_state.game_state
    
    elapsed = time.time() - st.session_state.start_time
    total_time = elapsed + st.session_state.penalty_time
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: st.markdown(f"**👤 {st.session_state.user_name}** ({st.session_state.setting_dan}단)")
    with c2: st.markdown(f"🎯 목표: **{st.session_state.caught_count} / {TARGET_COUNT}**")
    with c3: st.button("❌ 포기", on_click=go_home, use_container_width=True)

    st.markdown(f"""
        <div class="clock-container"><div class="clock-text">{total_time:.1f}</div></div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='question-box'>{game['problem']} = ?</div>", unsafe_allow_html=True)

    # --- 그리드 그리기 (강력한 CSS 적용) ---
    for row in range(3):
        cols = st.columns(3)
        for col in range(3):
            idx = row * 3 + col
            
            is_correct = (idx == game['correct_mole_idx'])
            is_wrong = (idx == game['wrong_mole_idx'])
            bg_url = mole_b64 if (is_correct or is_wrong) else hole_b64
            
            number = game['grid'][idx]
            btn_key = f"btn_{idx}"

            # ★ CSS: 특정 키를 가진 버튼에 강제로 이미지 주입 ★
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
            .st-key-{btn_key} button:hover {{
                background-color: rgba(0,0,0,0.1) !important;
            }}
            </style>
            """, unsafe_allow_html=True)
            
            with cols[col]:
                # 1. 투명한 버튼 (이미지는 CSS로 깔림) - 클릭 시 check_answer 즉시 실행
                st.button(" ", key=btn_key, on_click=check_answer, args=(idx,), use_container_width=True)
                
                # 2. 숫자 텍스트 (버튼 아래에 별도로 표시)
                st.markdown(f"<div class='number-label'>{number}</div>", unsafe_allow_html=True)

    # 키보드 입력
    st.write("")
    st.text_input("키패드", key="kbd_input", label_visibility="collapsed", on_change=process_input)
    
    time.sleep(0.1)
    st.rerun()

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
        st.button("🏠 처음으로 돌아가기", on_click=go_home, use_container_width=True, type="primary")
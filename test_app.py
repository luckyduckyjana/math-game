import streamlit as st
import random
import time
import base64
import os

# --- 1. 설정 및 이미지 로드 ---
st.set_page_config(page_title="럭키덕키 구구단", page_icon="🐹", layout="centered")

# 이미지 경로 (images 폴더 확인 필수)
IMG_DIR = "images"
MOLE_IMG_PATH = os.path.join(IMG_DIR, "mole.png")  # 두더지
HOLE_IMG_PATH = os.path.join(IMG_DIR, "hole.jpg")  # 구덩이

# 이미지 Base64 변환 함수
def get_base64_image(path):
    if not os.path.exists(path): return None
    with open(path, 'rb') as f: data = f.read()
    return base64.b64encode(data).decode()

mole_b64 = get_base64_image(MOLE_IMG_PATH)
hole_b64 = get_base64_image(HOLE_IMG_PATH)
images_ready = mole_b64 is not None and hole_b64 is not None

# --- 2. CSS 스타일링 ---
st.markdown(f"""
    <style>
    /* 전체 배경: 흙색 */
    .stApp {{ background-color: #8D6E63; }}
    
    /* 숫자 텍스트 스타일 (구덩이 아래) */
    .number-label {{
        text-align: center;
        font-size: 30px; /* 숫자를 더 크게! */
        font-weight: bold;
        color: white;
        text-shadow: 2px 2px 4px #000000;
        margin-top: -10px;
        margin-bottom: 20px;
        font-family: 'Comic Sans MS', sans-serif;
    }}

    /* 문제 박스 */
    .question-box {{
        text-align: center; font-size: 45px; font-weight: bold;
        color: #3E2723; background: #FFECB3;
        border: 4px solid #FFD54F; border-radius: 15px;
        padding: 15px; margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }}
    
    /* 버튼 공통 스타일 리셋 */
    .stButton > button {{
        width: 100%;
        height: 110px; /* 버튼 높이 */
        border: none !important;
        background-color: transparent !important; /* 배경 투명 */
        transition: transform 0.1s;
    }}
    .stButton > button:active {{ transform: scale(0.90); }} /* 클릭 시 눌리는 효과 */
    
    </style>
""", unsafe_allow_html=True)

# --- 3. 게임 로직 ---

def init_game():
    if 'score' not in st.session_state: st.session_state.score = 0
    if 'fails' not in st.session_state: st.session_state.fails = 0
    if 'game_state' not in st.session_state: st.session_state.game_state = None
    if 'difficulty_limit' not in st.session_state: st.session_state.difficulty_limit = 9999.0

def generate_new_problem(dan):
    multiplier = random.randint(1, 9)
    answer = dan * multiplier
    
    # 1. 9개의 숫자 생성 (정답 1개 + 오답 8개)
    grid_numbers = [answer]
    while len(grid_numbers) < 9:
        wrong = random.randint(1, 81)
        if wrong != answer and wrong not in grid_numbers:
            grid_numbers.append(wrong)
    random.shuffle(grid_numbers)
    
    # 2. 정답 위치 찾기
    answer_idx = grid_numbers.index(answer)
    
    # 3. 두더지 위치 선정 (총 3마리: 정답 1 + 오답 2)
    all_indices = list(range(9))
    all_indices.remove(answer_idx)
    distraction_moles = random.sample(all_indices, 2)
    mole_indices = set([answer_idx] + distraction_moles)
    
    return {
        'problem': f"{dan} x {multiplier}",
        'answer': answer,
        'grid': grid_numbers,
        'mole_indices': mole_indices,
        'answer_idx': answer_idx,
        'start_time': time.time()
    }

def check_answer(idx):
    current = st.session_state.game_state
    limit = st.session_state.difficulty_limit
    
    # 시간 초과 체크
    if time.time() - current['start_time'] > limit:
        st.toast("⏰ 시간 초과! 두더지들이 도망갔어요!", icon="💨")
        st.session_state.game_state = generate_new_problem(st.session_state.dan)
        return

    selected_num = current['grid'][idx]
    
    # 1. 정답 칸 (점수 +)
    if idx == current['answer_idx']:
        st.session_state.score += 10
        st.toast("정답! 잡았다 요놈! 🔨 (+10점)", icon="🐹")
        st.session_state.game_state = generate_new_problem(st.session_state.dan)
        
    # 2. 오답인데 두더지 (감점 -)
    elif idx in current['mole_indices']:
        st.session_state.fails += 1
        st.session_state.score = max(0, st.session_state.score - 5)
        st.toast(f"으악! {selected_num}은(는) 함정이에요!", icon="💥")
        
    # 3. 빈 구덩이 (감점 -)
    else:
        st.session_state.fails += 1
        st.session_state.score = max(0, st.session_state.score - 5)
        st.toast(f"거긴 아무것도 없어요!", icon="❌")

# --- 4. 메인 화면 ---

init_game()
st.markdown("<h1 style='text-align:center; color:#FFD54F; text-shadow: 2px 2px 4px #3E2723;'>🐹 럭키덕키 구구단</h1>", unsafe_allow_html=True)

if not images_ready:
    st.error("⚠️ 이미지 로드 실패! images 폴더에 mole.png, hole.jpg가 있는지 확인하세요.")
    st.stop()

# 상단 설정 바
col1, col2, col3 = st.columns([1, 2, 2])
with col1:
    st.session_state.dan = st.selectbox("몇 단?", range(2, 10))
with col2:
    diff = st.radio("난이도", ["쉬움", "보통(5초)", "어려움(3초)"], label_visibility="collapsed")
    limit = 9999.0
    if "보통" in diff: limit = 5.0
    elif "어려움" in diff: limit = 3.0
    st.session_state.difficulty_limit = limit
with col3:
    st.markdown(f"<div style='background:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold;'>🏆 {st.session_state.score}점 | ❌ {st.session_state.fails}회</div>", unsafe_allow_html=True)

# 게임 데이터 초기화
if st.session_state.game_state is None:
    st.session_state.game_state = generate_new_problem(st.session_state.dan)
game = st.session_state.game_state

# 시간 게이지
if limit < 100:
    left = max(0.0, limit - (time.time() - game['start_time']))
    st.progress(left / limit)
    if left == 0: st.rerun()

# 문제 표시
st.markdown(f"<div class='question-box'>{game['problem']} = ?</div>", unsafe_allow_html=True)

# --- 그리드 및 버튼 생성 ---
# 3x3 그리드 생성
for row in range(3):
    cols = st.columns(3)
    for col in range(3):
        idx = row * 3 + col
        number = game['grid'][idx]
        
        # 두더지 출몰 여부 확인
        is_mole = idx in game['mole_indices']
        
        # 이미지 선택
        current_bg = mole_b64 if is_mole else hole_b64
        mime_type = "image/png" if is_mole else "image/jpeg"
        
        # ★ CSS로 버튼 배경 입히기 ★
        button_key = f"btn_{idx}"
        st.markdown(f"""
        <style>
        .st-key-{button_key} button {{
            background-image: url("data:{mime_type};base64,{current_bg}") !important;
            background-size: contain !important; /* 이미지가 잘리지 않게 contain or cover */
            background-repeat: no-repeat !important;
            background-position: center bottom !important;
            box-shadow: none !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        with cols[col]:
            # 1. 이미지 버튼 (클릭 시 동작)
            if st.button(" ", key=button_key, use_container_width=True):
                check_answer(idx)
                st.rerun()
            
            # 2. 숫자 표시 (버튼 아래)
            st.markdown(f"<div class='number-label'>{number}</div>", unsafe_allow_html=True)

st.write("---")
st.caption("made by LuckyDucky Game Studio 🎲")
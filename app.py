import streamlit as st
import google.generativeai as genai
from PIL import Image
from duckduckgo_search import DDGS

# 1. API 설정 (스트림릿 비밀 금고에서 가져오기)
API_KEY = st.secrets["API_KEY"]
genai.configure(api_key=API_KEY)

# 2. 모델 설정
model = genai.GenerativeModel('models/gemini-2.5-flash')

# 3. 이미지 검색 함수
def search_art_image(query):
    try:
        with DDGS() as ddgs:
            search_results = ddgs.images(f"{query} artwork", max_results=1)
            if search_results:
                return search_results[0]['image']
    except Exception as e:
        return None
    return None

# 4. 화면 기본 설정
st.set_page_config(page_title="미술 탐험대", page_icon="🎨", layout="centered")

# --- 🧠 5. 대화 기억 장치 (Session State) 만들기 ---
# 사용자와 주고받은 대화와 사진을 새로고침해도 날아가지 않게 보관합니다.
if "messages" not in st.session_state:
    st.session_state.messages = []       # 대화 기록 저장
if "current_image" not in st.session_state:
    st.session_state.current_image = None # 현재 보고 있는 사진 저장
if "artwork_name" not in st.session_state:
    st.session_state.artwork_name = ""   # 현재 작품 이름 기억

# 화면 제목
st.title("🎨 미술 탐험대: 쉬운 미술 해설!")
st.write("안녕! 궁금한 미술 작품을 검색하고, 선생님과 자유롭게 대화도 나눠보자. 😉")

# 사용자 입력창
search_query = st.text_input("🔍 작품 이름이나 작가 (예: 고흐 해바라기)")
uploaded_file = st.file_uploader("🖼️ 또는 사진을 올려주세요!", type=["jpg", "png", "jpeg"])

prompt_text = """
너는 친절하고 재미있는 초등학교 미술 선생님이야. 
초등학교 5학년 학생이 이해하기 쉽게 핵심만 설명해 줘. 
어려운 용어는 피하고, 친근하게 대화하는 말투(~했단다, ~해 볼까?)를 사용해.
"""

# --- 🎯 6. 새로운 작품 해설 시작 ---
if st.button("✨ 새로운 해설 듣기 (새 대화 시작)"):
    # 다른 작품을 검색하면 기존 대화 기록을 싹 지우고 새 출발합니다!
    st.session_state.messages = []
    st.session_state.current_image = None
    st.session_state.artwork_name = search_query if search_query else "업로드한 사진"

    if uploaded_file is not None:
        with st.spinner('선생님이 사진을 보고 있어요...'):
            image = Image.open(uploaded_file)
            st.session_state.current_image = image # 기억 장치에 사진 저장
            try:
                response = model.generate_content([prompt_text, image])
                # AI의 첫 번째 해설을 대화 기록에 저장
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"오류가 발생했어요: {e}")

    elif search_query:
        with st.spinner('사진과 해설을 찾고 있어요...'):
            try:
                art_image_url = search_art_image(search_query)
                st.session_state.current_image = art_image_url # 기억 장치에 URL 저장
                
                response = model.generate_content([prompt_text, f"작품 이름: {search_query}"])
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"오류가 발생했어요: {e}")
    else:
        st.warning("작품 이름을 적거나 사진을 먼저 올려주세요!")

st.write("---")

# --- 🖼️ 7. 기억해둔 사진 보여주기 ---
if st.session_state.current_image is not None:
    st.image(st.session_state.current_image, use_container_width=True)
elif st.session_state.current_image is None and len(st.session_state.messages) > 0 and st.session_state.artwork_name != "업로드한 사진":
     st.warning("⚠️ 검색 엔진 보안 문제로 사진을 자동으로 불러오지 못했어요.")

# --- 💬 8. 지금까지의 대화 기록 화면에 보여주기 ---
for msg in st.session_state.messages:
    # 학생은 손드는 이모티콘 🙋‍♂️, 선생님은 화가 이모티콘 👩‍🎨
    avatar_icon = "🙋‍♂️" if msg["role"] == "user" else "👩‍🎨"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

# --- 🙋‍♂️ 9. 아이들이 추가 질문하는 채팅창 ---
# 대화가 1개 이상 있을 때(해설을 한 번이라도 들었을 때)만 질문 창이 맨 아래에 나타납니다.
if len(st.session_state.messages) > 0:
    if user_question := st.chat_input("선생님에게 더 궁금한 점을 물어보세요!"):
        
        # 1. 학생의 질문을 화면에 표시하고 기록에 저장
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user", avatar="🙋‍♂️"):
            st.markdown(user_question)
            
        # 2. 선생님(AI)의 대답 준비
        with st.chat_message("assistant", avatar="👩‍🎨"):
            with st.spinner("선생님이 생각 중이에요..."):
                # 지금까지의 대화 내용을 하나의 글로 묶어서 AI에게 전달합니다.
                history_text = f"현재 대화 중인 작품: {st.session_state.artwork_name}\n\n"
                for m in st.session_state.messages:
                    speaker = "학생" if m["role"] == "user" else "선생님"
                    history_text += f"{speaker}: {m['content']}\n"
                
                chat_prompt = f"""
                너는 친절하고 재미있는 초등학교 미술 선생님이야. 지금 5학년 학생과 대화하고 있어.
                아래의 [지금까지의 대화 내용]을 읽고, 학생의 마지막 질문에 다정하게 대답해 줘.
                어려운 말은 쓰지 말고 대화하듯이 짧고 친절하게 대답해 줘.
                
                [지금까지의 대화 내용]
                {history_text}
                """
                
                try:
                    response = model.generate_content(chat_prompt)
                    st.markdown(response.text)
                    # 선생님의 대답도 기록에 저장
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error("앗, 대답을 생각하다가 오류가 났어요. 다시 시도해 주세요!")
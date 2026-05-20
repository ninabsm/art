import streamlit as st
import google.generativeai as genai
from PIL import Image
from duckduckgo_search import DDGS

# 1. Gemini API 키 설정 (선생님의 진짜 키로 변경해 주세요!)
API_KEY = st.secrets["API_KEY"]
genai.configure(api_key=API_KEY)

# 2. 사용할 Gemini 모델 불러오기
model = genai.GenerativeModel('models/gemini-2.5-flash')

# 3. 🛡️ 에러가 나도 프로그램이 멈추지 않는 이미지 검색 함수
def search_art_image(query):
    try:
        with DDGS() as ddgs:
            search_results = ddgs.images(f"{query} artwork", max_results=1)
            if search_results:
                return search_results[0]['image']
    except Exception as e:
        # 403 차단 등 에러가 발생하면 에러를 뿜지 않고 그냥 None(없음)을 반환합니다.
        return None
    return None

# 4. 웹앱 화면 구성
st.set_page_config(page_title="미술 탐험대", page_icon="🎨", layout="centered")
st.title("🎨 미술 탐험대: 쉬운 미술 해설!")
st.write("안녕! 궁금한 미술 작품의 이름이나 작가를 적어주거나, 사진을 올려주면 쉽고 재미있게 설명해 줄게. 😉")

# 5. 사용자 입력 받기
search_query = st.text_input("🔍 작품 이름이나 작가 이름을 적어주세요 (예: 고흐 해바라기)")
st.write("---")
uploaded_file = st.file_uploader("🖼️ 또는 미술 작품 사진을 올려주세요!", type=["jpg", "png", "jpeg"])

# 6. 초등학교 5학년 맞춤형 프롬프트(명령어)
prompt_text = """
너는 친절하고 재미있는 초등학교 미술 선생님이야. 
내가 보여주는 사진이나 말해주는 작품에 대해 초등학교 5학년 학생이 이해하기 쉽게 설명해 줘. 
어려운 미술 용어는 피하거나 아주 쉽게 풀어서 설명하고, 아이들이 흥미를 가질 만한 재미있는 이야기나 비유를 넣어줘. 
딱딱한 백과사전 말투가 아니라, 친근하게 대화하는 말투(~했단다, ~해 볼까?)를 사용해.
설명은 너무 길지 않게 핵심만 재미있게 해 줘.
"""

# 7. '해설 듣기' 버튼을 눌렀을 때의 동작
if st.button("✨ 해설 듣기"):
    
    # 7-1. 사진을 직접 올렸을 때
    if uploaded_file is not None:
        with st.spinner('선생님이 사진을 보고 해설을 준비하고 있어요...'):
            image = Image.open(uploaded_file)
            st.image(image, caption="업로드한 사진", use_container_width=True)
            try:
                response = model.generate_content([prompt_text, image])
                st.success("해설이 도착했어요!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"해설 도중 오류가 발생했어요: {e}")

    # 7-2. 글자로 검색했을 때
    elif search_query:
        with st.spinner('미술 선생님이 사진과 해설을 모두 찾고 있어요...'):
            try:
                # 인터넷에서 작품 사진 검색 (차단당하면 None이 돌아옴)
                art_image_url = search_art_image(search_query)
                
                # Gemini 해설은 사진 검색 성공 여부와 상관없이 무조건 실행!
                response = model.generate_content([prompt_text, f"작품 이름: {search_query}"])
                
                st.success("해설을 준비했어요! 👍")
                
                # 🚀 사진을 가져오는 데 성공했다면 화면에 표시
                if art_image_url:
                    st.image(art_image_url, caption=f"'{search_query}' 검색 결과", use_container_width=True)
                # 🚀 만약 검색 엔진에 차단당해서 사진을 못 가져왔다면 우회 링크 제공!
                else:
                    st.warning(f"⚠️ 검색 엔진 보안 문제로 사진을 자동으로 불러오지 못했어요.")
                    # 구글 이미지 검색 링크를 만들어 줍니다.
                    google_search_url = f"https://www.google.com/search?tbm=isch&q={search_query}"
                    st.markdown(f"💡 **[여기 구글 이미지 검색 창(클릭)]({google_search_url})**을 열어서 사진을 함께 보며 아래 해설을 읽어보세요!")
                
                # 해설 출력
                st.write("---")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"오류가 발생했어요: {e}")
                
    else:
        st.warning("작품 이름을 적거나 사진을 먼저 올려주세요!")
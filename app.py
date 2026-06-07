# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client, Client
import google.genai as genai
from PIL import Image

# 1. 웹페이지 기본 설정 (브라우저 탭에 표시될 이름)
st.set_page_config(page_title="사내 AI 지출증빙 시스템", page_icon="🧾", layout="centered")

SUPABASE_URL = "https://dactmkqrckxzacrcihgc.supabase.co"
SUPABASE_ANON_KEY = "여기에_Publishable_key_복사_붙여넣기"


# 중앙 서버에서 키를 원격으로 안전하게 로드하는 함수
@st.cache_resource  # 웹페이지가 새로고침되어도 키를 매번 서버에서 다시 받지 않도록 캐싱합니다.
def load_gemini_key():
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        response = supabase.table("app_config").select("key_value").eq("key_name", "GEMINI_API_KEY").execute()
        if response.data:
            return str(response.data[0]['key_value']).strip()
    except Exception as e:
        st.error(f"중앙 보안 서버 인증 실패: {e}")
    return None


# 웹 화면 UI 디자인
st.title("🧾 사내 AI 지출증빙 시스템")
st.markdown("스마트폰으로 찍은 영수증이나 캡처본을 올리면 AI가 즉시 세무 항목을 분석합니다.")
st.divider()

# API 키 확인
gemini_key = load_gemini_key()

if not gemini_key:
    st.warning("⚠️ 시스템 준비 중: 관리자 인증 동기화가 필요합니다.")
else:
    # 2. 파일 업로드 컴포넌트 (웹 브라우저에 파일 드래그 앤 드롭 창 생성)
    uploaded_file = st.file_uploader("영수증 이미지를 선택하거나 여기로 끌어다 놓으세요.", type=["png", "jpg", "jpeg", "webp"])

    if uploaded_file is not None:
        # 이미지 열기 및 화면 표시
        image = Image.open(uploaded_file)
        st.image(image, caption="업로드된 영수증", use_container_width=True)

        # 분석 시작 버튼
        if st.button("🤖 AI 영수증 자동 분석 시작", type="primary"):
            with st.spinner("제미나이 AI가 영수증 텍스트와 적격 증빙 여부를 판단하고 있습니다..."):
                try:
                    # 제미나이 초기화 및 프롬프트 주입
                    client = genai.Client(api_key=gemini_key)

                    prompt = """
                    이 영수증 이미지에서 다음 핵심 정보들을 노이즈 없이 명확하게 추출해서 보기 좋게 표나 항목으로 정리해줘.

                    1. 상호명 (가게 이름) 및 가맹점 주소
                    2. 사업자등록번호
                    3. 거래 일시 (연-월-일 시:분:초 형식)
                    4. 결제 금액 구조 (공급가액 / 부가세 / 총 합계금액 구분)
                    5. 결제 수단 (카드사 이름 및 카드번호 일부, 승인번호)
                    6. 품목 상세 리스트 (구매 항목, 수량, 단가 목록)
                    7. 적격 증빙 검토 의견: (이 영수증이 회사 세무 비용 처리를 위한 세금계산서, 법인카드 영수증, 현금영수증 등의 적격 증빙 요건을 충족하는지 종합 의견을 1줄 요약해줘)
                    """

                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[image, prompt]
                    )

                    st.success("📊 분석이 완료되었습니다!")
                    st.markdown("### 🤖 AI 영수증 분석 결과 보고서")
                    st.info(response.text)

                except Exception as e:
                    st.error(f"AI 분석 중 오류가 발생했습니다: {e}")
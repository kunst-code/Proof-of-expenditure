# -*- coding: utf-8 -*-
import os
import streamlit as st
from supabase import create_client, Client
import google.genai as genai
from PIL import Image

# 브라우저 및 서버 기본 설정
st.set_page_config(page_title="사내 AI 지출증빙 시스템", page_icon="🧾", layout="centered")

# ======================================================================
# ⚠️ [핵심 체크]: 큰따옴표 안에 주소와 anon 키를 정확하게 적어줍니다.
# ======================================================================
SUPABASE_URL = "https://dactmkqrckxzacrcihgc.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_PCH09T4MVJ7uCQhyll-VtQ_pB1MnRJm"


# 좀비 캐시 방지를 위해 @st.cache_resource를 완전히 삭제하고,
# 사이트가 켜질 때마다 무조건 주소를 실시간으로 새로 읽게 만듭니다.
def load_gemini_key():
    try:
        url = str(SUPABASE_URL).strip()
        anon_key = str(SUPABASE_ANON_KEY).strip()

        supabase: Client = create_client(url, anon_key)
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

# 무조건 실시간으로 Supabase에서 API 키를 받아옵니다.
gemini_key = load_gemini_key()

if not gemini_key:
    st.warning("⚠️ 시스템 준비 중: 관리자 인증 동기화가 필요합니다.")
else:
    # 파일 업로드 활성화
    uploaded_file = st.file_uploader("영수증 이미지를 선택하세요.", type=["png", "jpg", "jpeg", "webp"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="업로드된 영수증", use_container_width=True)

        if st.button("🤖 AI 영수증 자동 분석 시작", type="primary"):
            with st.spinner("제미나이 AI가 영수증을 정밀 분석 중입니다..."):
                try:
                    client = genai.Client(api_key=gemini_key)
                    prompt = """
                    이 영수증 이미지에서 다음 핵심 정보들을 명확하게 추출해서 보기 좋게 정리해줘.

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
                    st.success("📊 분석 완료!")
                    st.markdown("### 🤖 AI 영수증 분석 결과 보고서")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"AI 분석 실패: {e}")
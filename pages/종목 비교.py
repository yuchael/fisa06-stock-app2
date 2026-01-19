# ===============================
# 표준 라이브러리
# ===============================
import datetime

# ===============================
# 서드파티 라이브러리
# ===============================
import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# ===============================
# Matplotlib 한글 폰트 설정 (Windows)
# ===============================
font_path = "C:/Windows/Fonts/malgun.ttf"
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)
plt.rcParams['axes.unicode_minus'] = False

# ===============================
# Streamlit 기본 설정
# ===============================
st.set_page_config(
    page_title="종목 비교",
    page_icon="📊",
    layout="wide"
)

st.title("📊 종목 비교")

# ===============================
# KRX 상장사 리스트 (일반 주식만)
# ===============================
@st.cache_data
def get_krx_company_list() -> pd.DataFrame:
    url = "http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"
    df = pd.read_html(url, header=0, encoding="EUC-KR")[0]

    df = df[['회사명', '종목코드']]
    df['종목코드'] = df['종목코드'].astype(str)

    # ✅ 핵심: 숫자 6자리 종목만 필터링 (ETF/ETN/리츠 제거)
    df = df[df['종목코드'].str.match(r'^\d{6}$')]

    return df.reset_index(drop=True)

company_df = get_krx_company_list()
company_df['display'] = company_df['회사명'] + " (" + company_df['종목코드'] + ")"

# ===============================
# 종목 선택
# ===============================
col1, col2 = st.columns(2)

with col1:
    stock_a = st.selectbox(
        "종목 A 선택",
        company_df['display'],
        index=None,
        placeholder="첫 번째 종목 선택"
    )

with col2:
    stock_b = st.selectbox(
        "종목 B 선택",
        company_df['display'],
        index=None,
        placeholder="두 번째 종목 선택"
    )

# ===============================
# 기간 선택
# ===============================
today = datetime.date.today()
start_date, end_date = st.date_input(
    "비교 기간 선택",
    (today.replace(year=today.year - 1), today)
)

compare_btn = st.button("비교하기")

# ===============================
# 비교 로직
# ===============================
if compare_btn:
    if not stock_a or not stock_b:
        st.warning("비교할 두 종목을 모두 선택하세요.")
    else:
        try:
            with st.spinner("데이터를 불러오는 중..."):
                name_a, code_a = stock_a.split(" (")
                code_a = code_a.replace(")", "")

                name_b, code_b = stock_b.split(" (")
                code_b = code_b.replace(")", "")

                df_a = fdr.DataReader(
                    code_a,
                    start_date.strftime("%Y%m%d"),
                    end_date.strftime("%Y%m%d")
                )

                df_b = fdr.DataReader(
                    code_b,
                    start_date.strftime("%Y%m%d"),
                    end_date.strftime("%Y%m%d")
                )

            if df_a.empty or df_b.empty:
                st.error("선택한 기간에 데이터가 없습니다.")
            else:
                # 날짜 맞추기
                df = pd.DataFrame({
                    name_a: df_a['Close'],
                    name_b: df_b['Close']
                }).dropna()

                # 정규화 (시작값 = 100)
                norm_df = df / df.iloc[0] * 100

                # 📈 그래프
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.plot(norm_df.index, norm_df[name_a], label=name_a, linewidth=2.5)
                ax.plot(norm_df.index, norm_df[name_b], label=name_b, linewidth=2.5)

                ax.set_title("종목 성과 비교 (시작값 = 100)", fontsize=16)
                ax.set_ylabel("정규화된 주가")
                ax.grid(True, linestyle="--", alpha=0.4)
                ax.legend()
                fig.autofmt_xdate()

                st.pyplot(fig, use_container_width=True)

                # 📊 누적 수익률 요약
                returns = pd.DataFrame({
                    "종목": [name_a, name_b],
                    "누적 수익률 (%)": [
                        (df[name_a].iloc[-1] / df[name_a].iloc[0] - 1) * 100,
                        (df[name_b].iloc[-1] / df[name_b].iloc[0] - 1) * 100
                    ]
                })

                st.subheader("📌 기간 누적 수익률")
                st.dataframe(
                    returns.style.format({"누적 수익률 (%)": "{:.2f}%"})
                )

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

"""Screener - 投資補助ツール

メインアプリケーションエントリーポイント
"""

import streamlit as st

from db.database import init_db

# ─── ページ設定 ───
st.set_page_config(
    page_title="Screener - 投資補助ツール",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── DB初期化 ───
init_db()

# ─── サイドバー ───
with st.sidebar:
    st.title("📊 Screener")
    st.caption("投資補助ツール")
    st.divider()

    page = st.radio(
        "メニュー",
        ["🏠 ダッシュボード", "🔍 スクリーナー", "📈 銘柄詳細", "📄 決算分析", "⚙️ 設定"],
        label_visibility="collapsed",
    )

# ─── メインコンテンツ ───
if page == "🏠 ダッシュボード":
    st.title("🏠 ダッシュボード")
    st.info("開発中: ここに市場概要、注目銘柄、直近の決算分析結果を表示します。")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("日経平均", "---", "---")
    with col2:
        st.metric("TOPIX", "---", "---")
    with col3:
        st.metric("分析済み銘柄数", "---")
    with col4:
        st.metric("注目銘柄数", "---")

elif page == "🔍 スクリーナー":
    st.title("🔍 スクリーナー")
    st.info("開発中: テクニカル・ファンダメンタル条件でのスクリーニング機能を実装予定。")

elif page == "📈 銘柄詳細":
    st.title("📈 銘柄詳細")
    stock_code = st.text_input("銘柄コードを入力", placeholder="例: 7203")
    if stock_code:
        st.info(f"銘柄コード {stock_code} の詳細情報を表示予定。")

elif page == "📄 決算分析":
    st.title("📄 決算分析")
    st.info("開発中: TDnetからの決算資料取得、AI分析結果の表示を実装予定。")

elif page == "⚙️ 設定":
    st.title("⚙️ 設定")

    with st.expander("J-Quants API", expanded=True):
        st.text_input("メールアドレス", type="default", key="jquants_email")
        st.text_input("パスワード", type="password", key="jquants_password")
        st.selectbox("プラン", ["free", "standard"], key="jquants_plan")

    with st.expander("Gemini API"):
        st.text_input("APIキー", type="password", key="gemini_api_key")

    if st.button("設定を保存", type="primary"):
        st.success("設定を保存しました（.envファイルへの反映は手動で行ってください）。")

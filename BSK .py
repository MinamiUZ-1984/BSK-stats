import streamlit as st
import pandas as pd

st.set_page_config(page_title="バスケ分析レポート", layout="wide")

# --- データ管理 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Q', '名前', '項目', 'エリア', '結果', '点数'])
if 'current_q' not in st.session_state:
    st.session_state.current_q = "1Q"

PLAYERS = [f"{i}番" for i in range(1, 21)]

def record(item, name=None, area="-", result="成功", pts=0):
    p_name = name if name else st.session_state.selected_player
    new_data = pd.DataFrame([{'Q': st.session_state.current_q, '名前': p_name, '項目': item, 'エリア': area, '結果': result, '点数': pts}])
    st.session_state.history = pd.concat([st.session_state.history, new_data], ignore_index=True)
    st.toast(f"記録完了: {p_name}")

# --- メインナビゲーション ---
tab_input, tab_report = st.tabs(["✍️ 記録入力", "📋 試合レポート発行"])

# --- 【タブ1】記録入力画面 ---
with tab_input:
    st.session_state.current_q = st.radio("クォーター", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, key="q_radio")
    
    if st.button("⏱️ 24秒バイオレーション", use_container_width=True):
        record("24秒バイオ", name="TEAM", result="TO")

    st.write("### 選手を選択")
    p_cols = st.columns(5)
    for i, p in enumerate(PLAYERS):
        with p_cols[i % 5]:
            if st.button(p, key=f"p_{p}", use_container_width=True):
                st.session_state.selected_player = p

    if 'selected_player' in st.session_state:
        st.info(f"選択中: {st.session_state.selected_player}番")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🏀 2P成功", use_container_width=True, type="primary"): record("2P", result="成功", pts=2)
            if st.button("🎯 3P成功", use_container_width=True, type="primary"): record("3P", result="成功", pts=3)
        with c2:
            if st.button("❌ 2P失敗", use_container_width=True): record("2P", result="失敗")
            if st.button("❌ 3P失敗", use_container_width=True): record("3P", result="失敗")
        with c3:
            if st.button("🚨 ファール", use_container_width=True): record("ファール")
            if st.button("✨ アシスト", use_container_width=True): record("AST")
        
        st.write("リバウンド / その他")
        c4, c5, c6 = st.columns(3)
        with c4:
            if st.button("💪 OR", use_container_width=True): record("OR")
        with c5:
            if st.button("🛡️ DR", use_container_width=True): record("DR")
        with c6:
            if st.button("⚠️ TO", use_container_width=True): record("TO")

# --- 【タブ2】試合レポート画面 ---
with tab_report:
    if st.session_state.history.empty:
        st.warning("データがありません。入力を先に進めてください。")
    else:
        st.title("📊 GAME REPORT")
        
        # --- 1ページ目：表紙（サマリー） ---
        st.header("1. 試合サマリー")
        
        # クォーター別得点表
        q_scores = st.session_state.history.groupby('Q')['点数'].sum()
        st.subheader("【スコア推移】")
        st.table(pd.DataFrame(q_scores).T)
        
        # チーム合計スタッツ
        total_pts = st.session_state.history['点数'].sum()
        total_reb = st.session_state.history[st.session_state.history['項目'].isin(['OR', 'DR'])].shape[0]
        st.columns(2)[0].metric("チーム合計得点", f"{total_pts} 点")
        st.columns(2)[1].metric("チーム合計リバウンド", f"{total_reb} 本")

        st.divider()

        # --- 2ページ目：詳細スタッツ ---
        st.header("2. 個人詳細スタッツ")
        # 個人別の各項目を集計
        personal_stats = st.session_state.history.pivot_table(
            index='名前', columns='項目', aggfunc='size', fill_value=0
        )
        # 得点計算（pivot_tableには点数が含まれないので別途追加）
        personal_pts = st.session_state.history.groupby('名前')['点数'].sum()
        personal_stats['総得点'] = personal_pts
        
        st.dataframe(personal_stats, use_container_width=True)

        st.divider()

        # --- 3ページ目：全プレイログ ---
        st.header("3. プレイ詳細ログ")
        st.write("すべての記録を時系列で表示しています。")
        st.dataframe(st.session_state.history)

        # CSVダウンロードボタン（これを送ればExcelで開ける）
        csv = st.session_state.history.to_csv(index=False).encode('utf_8_sig')
        st.download_button("レポートをCSVでダウンロード", csv, "game_report.csv", "text/csv")

if st.sidebar.button("試合データをリセット"):
    st.session_state.history = pd.DataFrame(columns=['Q', '名前', '項目', 'エリア', '結果', '点数'])
    st.rerun()

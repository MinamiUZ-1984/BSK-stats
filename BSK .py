import streamlit as st
import pandas as pd

st.set_page_config(page_title="バスケスタッツ管理", layout="wide")
st.title("🏀 バスケ試合スタッツ管理システム")

# --- 1. メンバーリストの設定 (ここを書き換えれば名前を変えられます) ---
HOME_TEAM_NAME = "自チーム"
AWAY_TEAM_NAME = "相手チーム"

# 自チームの20名（名前を自由に変えてください）
HOME_PLAYERS = [f"選手 {i}" for i in range(1, 21)] 
# 相手チーム用（背番号などで管理する場合を想定）
AWAY_PLAYERS = [f"相手 #{i}" for i in range(1, 21)]

# --- 2. データの保存場所を準備 ---
if 'stats_data' not in st.session_state:
    # 'チーム' 列を追加
    st.session_state.stats_data = pd.DataFrame(
        columns=['チーム', '選手名', '得点', 'リバウンド', 'アシスト']
    )

# --- 3. サイドバー：データ入力エリア ---
with st.sidebar:
    st.header("📊 スタッツ入力")
    
    # チーム選択
    team_choice = st.radio("記録するチームを選択", [HOME_TEAM_NAME, AWAY_TEAM_NAME])
    
    # 選手選択（20名のリストから選ぶ）
    if team_choice == HOME_TEAM_NAME:
        player_name = st.selectbox("選手を選択", HOME_PLAYERS)
    else:
        player_name = st.selectbox("選手を選択", AWAY_PLAYERS)
    
    # 各スタッツ項目
    pts = st.number_input("得点", min_value=0, step=1)
    reb = st.number_input("リバウンド", min_value=0, step=1)
    ast = st.number_input("アシスト", min_value=0, step=1)

    if st.button("記録を保存"):
        new_entry = pd.DataFrame(
            [[team_choice, player_name, pts, reb, ast]], 
            columns=['チーム', '選手名', '得点', 'リバウンド', 'アシスト']
        )
        st.session_state.stats_data = pd.concat([st.session_state.stats_data, new_entry], ignore_index=True)
        st.success(f"{team_choice} {player_name} の記録を保存しました！")

# --- 4. メイン画面：スタッツ表示 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"🏠 {HOME_TEAM_NAME}")
    home_df = st.session_state.stats_data[st.session_state.stats_data['チーム'] == HOME_TEAM_NAME]
    st.table(home_df.drop(columns=['チーム']))
    st.metric("合計得点", home_df['得点'].sum())

with col2:
    st.subheader(f"🚌 {AWAY_TEAM_NAME}")
    away_df = st.session_state.stats_data[st.session_state.stats_data['チーム'] == AWAY_TEAM_NAME]
    st.table(away_df.drop(columns=['チーム']))
    st.metric("合計得点", away_df['得点'].sum())

# リセットボタン（全データを消去）
if st.button("全データをクリアして新しい試合を始める"):
    st.session_state.stats_data = pd.DataFrame(columns=['チーム', '選手名', '得点', 'リバウンド', 'アシスト'])
    st.rerun()

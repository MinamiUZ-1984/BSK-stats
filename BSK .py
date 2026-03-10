import streamlit as st
import pandas as pd

st.title("🏀 バスケ試合スタッツ管理")

if 'stats_data' not in st.session_state:
    st.session_state.stats_data = pd.DataFrame(columns=['選手名', '得点', 'リバウンド', 'アシスト'])

with st.sidebar:
    st.header("データ入力")
    name = st.text_input("選手名")
    points = st.number_input("得点", min_value=0, step=1)
    rebounds = st.number_input("リバウンド", min_value=0, step=1)
    assists = st.number_input("アシスト", min_value=0, step=1)

    if st.button("記録を保存"):
        new_data = pd.DataFrame([[name, points, rebounds, assists]], 
                                columns=['選手名', '得点', 'リバウンド', 'アシスト'])
        st.session_state.stats_data = pd.concat([st.session_state.stats_data, new_data], ignore_index=True)
        st.success(f"{name} 選手の記録を保存しました！")

st.header("試合スタッツ一覧")
if not st.session_state.stats_data.empty:
    st.dataframe(st.session_state.stats_data, use_container_width=True)
    st.metric("チーム合計得点", f"{st.session_state.stats_data['得点'].sum()} 点")
else:
    st.info("左のメニューから入力してください。")

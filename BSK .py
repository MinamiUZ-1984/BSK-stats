import streamlit as st
import pandas as pd

st.set_page_config(page_title="バスケ分析レポートPro", layout="wide")

# --- 1. データ保持の設定 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Q', 'チーム', '名前', '項目', '結果', '点数'])

# --- 2. サイドバー：試合基本情報 ---
with st.sidebar:
    st.header("📋 試合基本情報")
    game_date = st.date_input("試合日")
    home_name = st.text_input("自チーム名", "My Team")
    away_name = st.text_input("相手チーム名", "Opponent")
    
    st.divider()
    if st.button("試合データをすべて消去", type="secondary"):
        st.session_state.history = pd.DataFrame(columns=['Q', 'チーム', '名前', '項目', '結果', '点数'])
        st.rerun()

# --- 3. メイン画面のタブ構成 ---
tab_input, tab_report = st.tabs(["✍️ リアルタイム記録", "📄 試合分析レポート発行"])

# --- 【タブ1】記録入力画面 ---
with tab_input:
    col_q, col_t = st.columns(2)
    with col_q:
        current_q = st.radio("クォーター", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True)
    with col_t:
        current_team = st.radio("記録するチーム", [home_name, away_name], horizontal=True)

    st.divider()
    
    # 選手選択（20名分）
    players = [f"{i}番" for i in range(1, 21)]
    p_cols = st.columns(5)
    for i, p in enumerate(players):
        with p_cols[i % 5]:
            if st.button(p, key=f"p_{current_team}_{p}", use_container_width=True):
                st.session_state.selected_player = p

    if 'selected_player' in st.session_state:
        st.subheader(f"記録中: {current_team} - {st.session_state.selected_player}")
        
        def quick_record(item, res, pts):
            data = pd.DataFrame([{'Q': current_q, 'チーム': current_team, '名前': st.session_state.selected_player, '項目': item, '結果': res, '点数': pts}])
            st.session_state.history = pd.concat([st.session_state.history, data], ignore_index=True)
            st.toast(f"{item} {res}")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🏀 2P成功", use_container_width=True, type="primary"): quick_record("2P", "成功", 2)
            if st.button("❌ 2P失敗", use_container_width=True): quick_record("2P", "失敗", 0)
        with c2:
            if st.button("🎯 3P成功", use_container_width=True, type="primary"): quick_record("3P", "成功", 3)
            if st.button("❌ 3P失敗", use_container_width=True): quick_record("3P", "失敗", 0)
        with c3:
            if st.button("⚪ FT成功", use_container_width=True, type="primary"): quick_record("FT", "成功", 1)
            if st.button("❌ FT失敗", use_container_width=True): quick_record("FT", "失敗", 0)
        
        o1, o2, o3, o4, o5 = st.columns(5)
        with o1: 
            if st.button("OR", use_container_width=True): quick_record("OR", "成功", 0)
        with o2: 
            if st.button("DR", use_container_width=True): quick_record("DR", "成功", 0)
        with o3: 
            if st.button("AST", use_container_width=True): quick_record("AST", "成功", 0)
        with o4: 
            if st.button("STL", use_container_width=True): quick_record("STL", "成功", 0)
        with o5: 
            if st.button("🚨 F", use_container_width=True): quick_record("Foul", "なし", 0)

# --- 【タブ2】試合レポート画面 ---
with tab_report:
    if st.session_state.history.empty:
        st.info("データが入力されるとレポートが作成されます。")
    else:
        st.title(f"🏀 GAME ANALYSIS REPORT")
        st.caption(f"試合日: {game_date} | {home_name} vs {away_name}")
        
        # 1. スコアサマリー
        st.header("1. 試合経過・スコア")
        score_board = st.session_state.history.groupby(['Q', 'チーム'])['点数'].sum().unstack().fillna(0).astype(int)
        st.table(score_board.T)
        
        # 2. 個人ボックススコアの作成
        def build_boxscore(team_name):
            st.subheader(f"【{team_name} ボックススコア】")
            df = st.session_state.history[st.session_state.history['チーム'] == team_name]
            if df.empty: return st.write("データがありません")

            # 選手ごとに集計
            players_list = df['名前'].unique()
            rows = []
            for p in players_list:
                pdf = df[df['名前'] == p]
                
                # 各指標の算出
                m2_in = len(pdf[(pdf['項目'] == '2P') & (pdf['結果'] == '成功')])
                m2_att = len(pdf[pdf['項目'] == '2P'])
                m3_in = len(pdf[(pdf['項目'] == '3P') & (pdf['結果'] == '成功')])
                m3_att = len(pdf[pdf['項目'] == '3P'])
                ft_in = len(pdf[(pdf['項目'] == 'FT') & (pdf['結果'] == '成功')])
                ft_att = len(pdf[pdf['項目'] == 'FT'])
                
                fgm = m2_in + m3_in
                fga = m2_att + m3_att
                fg_pct = (fgm / fga * 100) if fga > 0 else 0
                
                rows.append({
                    '選手': p,
                    'PTS': pdf['点数'].sum(),
                    'FGM': fgm, 'FGA': fga, 'FG%': f"{fg_pct:.1f}%",
                    '3PM': m3_in, '3PA': m3_att,
                    'FTM': ft_in, 'FTA': ft_att,
                    'OR': len(pdf[pdf['項目'] == 'OR']),
                    'DR': len(pdf[pdf['項目'] == 'DR']),
                    'AST': len(pdf[pdf['項目'] == 'AST']),
                    'STL': len(pdf[pdf['項目'] == 'STL']),
                    'F': len(pdf[pdf['項目'] == 'Foul'])
                })
            
            box_df = pd.DataFrame(rows).set_index('選手')
            st.dataframe(box_df, use_container_width=True)

        build_boxscore(home_name)
        st.divider()
        build_boxscore(away_name)

        # CSV出力
        csv = st.session_state.history.to_csv(index=False).encode('utf_8_sig')
        st.download_button("レポート(CSV)を保存", csv, f"Report_{game_date}.csv", "text/csv")

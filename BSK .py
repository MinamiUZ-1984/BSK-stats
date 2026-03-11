import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="バスケ分析Pro", layout="centered")

# --- 1. データ保持の設定（初期化） ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['大会名', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state:
    st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state:
    st.session_state.tmp = {}
if 'current_q' not in st.session_state:
    st.session_state.current_q = "1Q"

# --- 2. サイドバー：詳細設定 ---
with st.sidebar:
    st.header("🏆 試合・チーム設定")
    tournament_name = st.text_input("大会名", "練習試合")
    game_date = st.date_input("試合日")
    
    st.divider()
    home_name = st.text_input("自チーム名", "HOME")
    default_nums = ",".join([str(i) for i in range(4, 24)])
    home_players_input = st.text_area("自チーム背番号 (カンマ区切り)", default_nums)
    home_players = [n.strip() for n in home_players_input.split(",") if n.strip()]

    st.divider()
    away_name = st.text_input("相手チーム名", "AWAY")
    away_players_input = st.text_area("相手チーム背番号 (カンマ区切り)", default_nums)
    away_players = [n.strip() for n in away_players_input.split(",") if n.strip()]

    st.divider()
    if st.button("全データを消去してリセット", type="secondary"):
        st.session_state.history = pd.DataFrame(columns=['大会名', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
        st.session_state.mode = "選手選択"
        st.session_state.tmp = {}
        st.rerun()

# --- 3. 共通記録関数（エラー防止ガード付き） ---
def record(item, detail="-", res="成功", pts=0):
    # 選手が選ばれていない場合は記録しない（エラー回避）
    if 'player' not in st.session_state.tmp or 'team' not in st.session_state.tmp:
        st.error("選手が選択されていません。選び直してください。")
        st.session_state.mode = "選手選択"
        return

    new_row = pd.DataFrame([{
        '大会名': tournament_name,
        'Q': st.session_state.current_q, 
        'チーム': st.session_state.tmp['team'], 
        '名前': f"{st.session_state.tmp['player']}番", 
        '項目': item, '詳細': detail, '結果': res, '点数': pts
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.session_state.mode = "選手選択"
    st.toast(f"記録：{st.session_state.tmp['team']} {st.session_state.tmp['player']}番")

# --- 4. メインタブ ---
tab_input, tab_report = st.tabs(["✍️ 記録入力", "📄 試合分析レポート"])

with tab_input:
    # Q選択
    st.session_state.current_q = st.radio("Q選択", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")
    st.divider()

    # --- A. 自チーム選手 ---
    st.write(f"🔵 **{home_name}**")
    h_cols = st.columns(5)
    for i, p_num in enumerate(home_players):
        with h_cols[i % 5]:
            if st.button(p_num, key=f"h_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': home_name}
                st.session_state.mode = "項目選択"

    # --- B. 操作パネル ---
    st.divider()
    container = st.container(border=True)
    with container:
        if st.session_state.mode == "選手選択":
            st.info("上下の選手をタップして記録開始")
        elif st.session_state.mode == "項目選択":
            st.subheader(f"⚡ {st.session_state.tmp.get('team')} #{st.session_state.tmp.get('player')}")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("2P", use_container_width=True, type="primary"):
                    st.session_state.tmp['item'] = "2P"; st.session_state.mode = "エリア選択"; st.rerun()
            with c2:
                if st.button("3P", use_container_width=True, type="primary"):
                    st.session_state.tmp['item'] = "3P"; st.session_state.mode = "エリア選択"; st.rerun()
            with c3:
                if st.button("FT", use_container_width=True):
                    st.session_state.tmp['item'] = "FT"; st.session_state.mode = "結果選択"; st.rerun()
            
            o1, o2, o3, o4 = st.columns(4)
            with o1: 
                if st.button("OR", use_container_width=True): record("OR")
                if st.button("DR", use_container_width=True): record("DR")
            with o2: 
                if st.button("AST", use_container_width=True): record("AST")
                if st.button("STL", use_container_width=True): record("STL")
            with o3: 
                if st.button("F", use_container_width=True): record("Foul")
                if st.button("BLK", use_container_width=True): record("BLK")
            with o4:
                if st.button("TV", use_container_width=True): record("TO", "TV")
                if st.button("DD", use_container_width=True): record("TO", "DD")
                if st.button("PM", use_container_width=True): record("TO", "PM")
            if st.button("× キャンセル", use_container_width=True): st.session_state.mode = "選手選択"; st.rerun()

        elif st.session_state.mode == "エリア選択":
            item_type = st.session_state.tmp.get('item', '2P')
            st.write(f"📍 エリア選択 ({item_type})")
            if item_type == "2P":
                areas = ["右ゴール下", "中ゴール下", "左ゴール下", "右レイアップ", "中レイアップ", "左レイアップ", "右コーナ", "右45deg", "中", "左45deg", "左コーナ"]
            else:
                areas = ["右コーナ3P", "右45deg3P", "中3P", "左45deg3P", "左コーナ3P"]
            
            a_cols = st.columns(2)
            for i, a in enumerate(areas):
                with a_cols[i % 2]:
                    if st.button(a, key=f"area_{i}", use_container_width=True):
                        st.session_state.tmp['area'] = a; st.session_state.mode = "結果選択"; st.rerun()
            if st.button("← 戻る"): st.session_state.mode = "項目選択"; st.rerun()

        elif st.session_state.mode == "結果選択":
            st.write(f"🎯 結果 ({st.session_state.tmp.get('area', 'FT')})")
            sc, fl = st.columns(2)
            item_type = st.session_state.tmp.get('item', '2P')
            pts = {"2P": 2, "3P": 3, "FT": 1}.get(item_type, 0)
            with sc:
                if st.button("SUCCESS", use_container_width=True, type="primary"):
                    record(item_type, detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts); st.rerun()
            with fl:
                if st.button("MISS", use_container_width=True):
                    record(item_type, detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0); st.rerun()
            if st.button("← 戻る"): st.session_state.mode = "項目選択"; st.rerun()

    st.divider()

    # --- C. 相手チーム選手 ---
    st.write(f"🔴 **{away_name}**")
    a_cols = st.columns(5)
    for i, p_num in enumerate(away_players):
        with a_cols[i % 5]:
            if st.button(p_num, key=f"a_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': away_name}
                st.session_state.mode = "項目選択"

# --- 5. レポートタブ ---
with tab_report:
    if st.session_state.history.empty:
        st.info("データが記録されるとここにレポートが表示されます。")
    else:
        st.title(f"📊 {tournament_name}")
        st.caption(f"試合日: {game_date} | {home_name} vs {away_name}")

        # --- ① クォーター別スコア表 ---
        st.header("1. スコア推移")
        try:
            q_scores = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0)
            q_order = ["1Q", "2Q", "3Q", "4Q", "OT"]
            q_scores = q_scores.reindex(columns=q_order, fill_value=0)
            q_scores['Total'] = q_scores.sum(axis=1)
            st.table(q_scores)
        except:
            st.write("スコア集計中...")

        # --- ② チームサマリー表 ---
        st.header("2. チームサマリー")
        def get_summary(t_name):
            df = st.session_state.history[st.session_state.history['チーム'] == t_name]
            if df.empty: return {"TEAM": t_name, "PTS": 0, "FG": "0-0", "FG%": "0%", "3P": "0-0", "FT": "0-0", "REB": 0, "AST": 0, "STL": 0, "TO": 0, "F": 0}
            fgm = len(df[((df['項目']=='2P') | (df['項目']=='3P')) & (df['結果']=='成功')])
            fga = len(df[(df['項目']=='2P') | (df['項目']=='3P')])
            m3in = len(df[(df['項目']=='3P') & (df['結果']=='成功')])
            m3at = len(df[df['項目']=='3P'])
            ftin = len(df[(df['項目']=='FT') & (df['結果']=='成功')])
            ftat = len(df[df['項目']=='FT'])
            return {
                "TEAM": t_name, "PTS": int(df['点数'].sum()), "FG": f"{fgm}-{fga}",
                "FG%": f"{(fgm/fga*100):.1f}%" if fga>0 else "0%",
                "3P": f"{m3in}-{m3at}", "FT": f"{ftin}-{ftat}",
                "REB": len(df[df['項目'].isin(['OR','DR'])]),
                "AST": len(df[df['項目']=='AST']), "STL": len(df[df['項目']=='STL']),
                "TO": len(df[df['項目']=='TO']), "F": len(df[df['項目']=='Foul'])
            }
        
        summary_data = []
        if home_name: summary_data.append(get_summary(home_name))
        if away_name: summary_data.append(get_summary(away_name))
        st.dataframe(pd.DataFrame(summary_data).set_index("TEAM"), use_container_width=True)

        st.divider()

        # --- ③ 個人ボックススコア ---
        st.header("3. 個人ボックススコア")
        def build_boxscore(t_name):
            st.write(f"#### 【{t_name}】")
            df = st.session_state.history[st.session_state.history['チーム'] == t_name]
            if df.empty:
                st.write("記録なし")
                return
            p_list = sorted(df['名前'].unique())
            rows = []
            for p in p_list:
                pdf = df[df['名前'] == p]
                m2in, m2at = len(pdf[(pdf['項目']=='2P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='2P'])
                m3in, m3at = len(pdf[(pdf['項目']=='3P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='3P'])
                ftin, ftat = len(pdf[(pdf['項目']=='FT') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='FT'])
                fgm, fga = m2in + m3in, m2at + m3at
                rows.append({
                    'No.': p, 'PTS': int(pdf['点数'].sum()),
                    'FGM': fgm, 'FGA': fga, 'FG%': f"{(fgm/fga*100):.1f}%" if fga>0 else "0%",
                    '3PM': m3in, '3PA': m3at, 'FTM': ftin, 'FTA': ftat,
                    'OR': len(pdf[pdf['項目']=='OR']), 'DR': len(pdf[pdf['項目']=='DR']),
                    'AST': len(pdf[pdf['項目']=='AST']), 'STL': len(pdf[pdf['項目']=='STL']),
                    'F': len(pdf[pdf['項目']=='Foul']), 'TO': len(pdf[pdf['項目']=='TO'])
                })
            st.dataframe(pd.DataFrame(rows).set_index('No.'), use_container_width=True)

        build_boxscore(home_name)
        st.divider()
        build_boxscore(away_name)

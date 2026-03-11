import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="バスケ分析Pro - 究極版", layout="centered")

# --- 1. データ保持の設定 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state:
    st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state:
    st.session_state.tmp = {}
if 'current_q' not in st.session_state:
    st.session_state.current_q = "1Q"
if 'memo' not in st.session_state:
    st.session_state.memo = ""

# --- 2. サイドバー：詳細設定 ---
with st.sidebar:
    st.header("🏆 試合・チーム設定")
    tournament_name = st.text_input("大会名", "練習試合")
    game_date = st.date_input("試合日")
    
    st.divider()
    home_name = st.text_input("自チーム名", "HOME")
    home_players_input = st.text_area("自チーム背番号 (カンマ区切り)", ",".join([str(i) for i in range(4, 24)]))
    home_players = [n.strip() for n in home_players_input.split(",") if n.strip()]

    st.divider()
    away_name = st.text_input("相手チーム名", "AWAY")
    away_players_input = st.text_area("相手チーム背番号 (カンマ区切り)", ",".join([str(i) for i in range(4, 24)]))
    away_players = [n.strip() for n in away_players_input.split(",") if n.strip()]

    st.divider()
    st.header("📝 コーチメモ")
    st.session_state.memo = st.text_area("試合の反省やメモ", st.session_state.memo)

    if st.button("全データをリセット", type="secondary"):
        st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
        st.session_state.mode = "選手選択"
        st.rerun()

# --- 3. 共通記録関数 ---
def record(item, detail="-", res="成功", pts=0):
    if 'player' not in st.session_state.tmp: return
    
    new_id = st.session_state.history['id'].max() + 1 if not st.session_state.history.empty else 1
    new_row = pd.DataFrame([{
        'id': new_id, 'Q': st.session_state.current_q, 
        'チーム': st.session_state.tmp['team'], 
        '名前': f"{st.session_state.tmp['player']}番", 
        '項目': item, '詳細': detail, '結果': res, '点数': pts
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.session_state.mode = "選手選択"
    st.toast(f"記録完了")

# --- 4. メインタブ ---
tab_input, tab_report, tab_edit = st.tabs(["✍️ 記録入力", "📄 分析レポート", "🛠 記録修正"])

# --- 【タブ1】記録入力 ---
with tab_input:
    # リアルタイム簡易スコア
    if not st.session_state.history.empty:
        qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0)
        qs = qs.reindex(columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
        qs['Total'] = qs.sum(axis=1)
        st.table(qs.astype(int))

    st.session_state.current_q = st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")
    st.divider()

    # --- 自チーム選手 (TOP) ---
    st.write(f"🔵 **{home_name}**")
    h_cols = st.columns(5)
    for i, p_num in enumerate(home_players):
        with h_cols[i % 5]:
            if st.button(p_num, key=f"h_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': home_name}
                st.session_state.mode = "項目選択"

    # --- 操作パネル (MIDDLE) ---
    st.divider()
    with st.container(border=True):
        if st.session_state.mode == "選手選択":
            st.info("選手をタップしてください")
        elif st.session_state.mode == "項目選択":
            st.subheader(f"⚡ {st.session_state.tmp.get('team')} #{st.session_state.tmp.get('player')}")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("2P", use_container_width=True, type="primary"): st.session_state.tmp['item']="2P"; st.session_state.mode="エリア選択"; st.rerun()
            with c2:
                if st.button("3P", use_container_width=True, type="primary"): st.session_state.tmp['item']="3P"; st.session_state.mode="エリア選択"; st.rerun()
            with c3:
                if st.button("FT", use_container_width=True): st.session_state.tmp['item']="FT"; st.session_state.mode="結果選択"; st.rerun()
            
            o_cols = st.columns(4)
            with o_cols[0]:
                if st.button("OR", use_container_width=True): record("OR")
                if st.button("DR", use_container_width=True): record("DR")
            with o_cols[1]:
                if st.button("AST", use_container_width=True): record("AST")
                if st.button("STL", use_container_width=True): record("STL")
            with o_cols[2]:
                if st.button("F", use_container_width=True): record("Foul")
                if st.button("BLK", use_container_width=True): record("BLK")
            with o_cols[3]:
                if st.button("TV", use_container_width=True): record("TO", "TV")
                if st.button("DD", use_container_width=True): record("TO", "DD")
                if st.button("PM", use_container_width=True): record("TO", "PM")
            if st.button("キャンセル", use_container_width=True): st.session_state.mode="選手選択"; st.rerun()

        elif st.session_state.mode == "エリア選択":
            it = st.session_state.tmp.get('item')
            if it == "2P":
                r1 = st.columns(3); r2 = st.columns(3); r3 = st.columns(5)
                for i, a in enumerate(["左ゴール下", "中ゴール下", "右ゴール下"]):
                    if r1[i].button(a, use_container_width=True): st.session_state.tmp['area']=a; st.session_state.mode="結果選択"; st.rerun()
                for i, a in enumerate(["左レイアップ", "中レイアップ", "右レイアップ"]):
                    if r2[i].button(a, use_container_width=True): st.session_state.tmp['area']=a; st.session_state.mode="結果選択"; st.rerun()
                for i, a in enumerate(["左角", "左45", "中", "右45", "右角"]):
                    if r3[i].button(a, use_container_width=True): st.session_state.tmp['area']=a; st.session_state.mode="結果選択"; st.rerun()
            else:
                r4 = st.columns(5)
                for i, a in enumerate(["左角3P", "左45 3P", "中 3P", "右45 3P", "右角3P"]):
                    if r4[i].button(a, use_container_width=True): st.session_state.tmp['area']=a; st.session_state.mode="結果選択"; st.rerun()
            if st.button("戻る"): st.session_state.mode="項目選択"; st.rerun()

        elif st.session_state.mode == "結果選択":
            st.write(f"🎯 {st.session_state.tmp.get('area', 'FT')}")
            sc, fl = st.columns(2)
            pts = {"2P": 2, "3P": 3, "FT": 1}.get(st.session_state.tmp.get('item'), 0)
            if sc.button("SUCCESS", use_container_width=True, type="primary"): record(st.session_state.tmp['item'], detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts); st.rerun()
            if fl.button("MISS", use_container_width=True): record(st.session_state.tmp['item'], detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0); st.rerun()
            if st.button("戻る"): st.session_state.mode="エリア選択" if "P" in st.session_state.tmp['item'] else "項目選択"; st.rerun()

    st.divider()
    # --- 相手チーム選手 (BOTTOM) ---
    st.write(f"🔴 **{away_name}**")
    a_cols = st.columns(5)
    for i, p_num in enumerate(away_players):
        with a_cols[i % 5]:
            if st.button(p_num, key=f"a_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': away_name}; st.session_state.mode = "項目選択"

# --- 【タブ2】分析レポート ---
with tab_report:
    if st.session_state.history.empty:
        st.info("データなし")
    else:
        st.title(f"📊 {tournament_name} レポート")
        st.caption(f"試合日: {game_date} | {home_name} vs {away_name}")
        
        # クォータースコア
        qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
        qs['Total'] = qs.sum(axis=1)
        st.table(qs.astype(int))

        # 個人ボックススコア + MVPロジック
        st.header("個人スタッツ")
        def build_box(t_name):
            df = st.session_state.history[st.session_state.history['チーム'] == t_name]
            if df.empty: return
            p_list = sorted(df['名前'].unique(), key=lambda x: int(x.replace('番', '')))
            rows = []
            for p in p_list:
                pdf = df[df['名前'] == p]
                m2in, m2at = len(pdf[(pdf['項目']=='2P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='2P'])
                m3in, m3at = len(pdf[(pdf['項目']=='3P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='3P'])
                ftin, ftat = len(pdf[(pdf['項目']=='FT') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='FT'])
                pts = pdf['点数'].sum()
                reb = len(pdf[pdf['項目'].isin(['OR','DR'])])
                ast = len(pdf[pdf['項目']=='AST'])
                stl = len(pdf[pdf['項目']=='STL'])
                # 簡易MVPスコア: (PTS+REB+AST+STL) - TO
                eff = pts + reb + ast + stl - len(pdf[pdf['項目']=='TO'])
                rows.append({'No.': p, 'PTS': pts, 'FG': f"{m2in+m3in}-{m2at+m3at}", '3P': f"{m3in}-{m3at}", 'REB': reb, 'AST': ast, 'STL': stl, 'F': len(pdf[pdf['項目']=='Foul']), 'TO': len(pdf[pdf['項目']=='TO']), '_eff': eff})
            
            box_df = pd.DataFrame(rows)
            max_eff = box_df['_eff'].max()
            box_df['MVP'] = box_df['_eff'].apply(lambda x: "👑" if x == max_eff and x > 0 else "")
            st.write(f"### {t_name}")
            st.dataframe(box_df[['MVP', 'No.', 'PTS', 'FG', '3P', 'REB', 'AST', 'STL', 'F', 'TO']].set_index('No.'), use_container_width=True)

        build_box(home_name); st.divider(); build_box(away_name)

        # シュートエリア分析 (視覚化)
        st.header("🎯 シュートエリア分析")
        shot_df = st.session_state.history[st.session_state.history['項目'].isin(['2P', '3P'])]
        if not shot_df.empty:
            area_stats = shot_df.groupby(['詳細', '結果']).size().unstack(fill_value=0)
            if '成功' not in area_stats: area_stats['成功'] = 0
            if '失敗' not in area_stats: area_stats['失敗'] = 0
            area_stats['成功率%'] = (area_stats['成功'] / (area_stats['成功'] + area_stats['失敗']) * 100).round(1)
            st.bar_chart(area_stats['成功率%'])
            st.dataframe(area_stats[['成功', '失敗', '成功率%']])

        if st.session_state.memo:
            st.info(f"📝 **コーチメモ:**\n{st.session_state.memo}")

# --- 【タブ3】記録修正 ---
with tab_edit:
    st.header("🛠 記録の修正・削除")
    if st.session_state.history.empty:
        st.write("データがありません")
    else:
        st.write("削除したい記録の「ゴミ箱ボタン」を押してください。")
        for i, row in st.session_state.history.iloc[::-1].iterrows():
            cols = st.columns([1, 4, 1])
            cols[0].write(f"#{row['id']}")
            cols[1].write(f"{row['Q']} | {row['名前']} | {row['項目']}({row['詳細']}) | {row['結果']}")
            if cols[2].button("🗑️", key=f"del_{row['id']}"):
                st.session_state.history = st.session_state.history.drop(i)
                st.rerun()

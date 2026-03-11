import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="バスケ分析Pro V02.7", layout="centered")

# --- 0. iPhone用レイアウト微調整 (CSS注入) ---
st.markdown("""
    <style>
    /* ボタンの余白と高さを詰める */
    .stButton > button {
        padding: 0.2rem 0.5rem !important;
        height: auto !important;
        min-height: 40px !important;
    }
    /* モバイルでもカラムを縦に並べず、横に維持する魔法のコード */
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
    /* タブの文字サイズ調整 */
    button[data-baseweb="tab"] {
        font-size: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. データ初期化 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state: st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state: st.session_state.tmp = {}
if 'current_q' not in st.session_state: st.session_state.current_q = "1Q"
if 'memo' not in st.session_state: st.session_state.memo = ""

# --- 2. サイドバー設定 ---
with st.sidebar:
    st.header("🏆 試合設定")
    tournament_name = st.text_input("大会名", "練習試合")
    game_date = st.date_input("試合日")
    st.divider()
    home_name = st.text_input("自チーム名", "HOME").strip()
    home_players = [n.strip() for n in st.text_area("自チーム背番号", ",".join([str(i) for i in range(4, 24)])).split(",") if n.strip()]
    st.divider()
    away_name = st.text_input("相手チーム名", "AWAY").strip()
    away_players = [n.strip() for n in st.text_area("相手チーム背番号", ",".join([str(i) for i in range(4, 24)])).split(",") if n.strip()]
    st.divider()
    st.session_state.memo = st.text_area("📝 コーチメモ", st.session_state.memo)
    if st.button("全リセット", type="secondary"):
        st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
        st.session_state.mode = "選手選択"; st.rerun()

# --- 3. 共通記録関数 ---
def record(item, detail="-", res="成功", pts=0, team=None, name=None):
    t_name = team if team else st.session_state.tmp.get('team', 'UNKNOWN')
    p_name = name if name else (f"{st.session_state.tmp['player']}番" if 'player' in st.session_state.tmp else "TEAM")
    new_id = st.session_state.history['id'].max() + 1 if not st.session_state.history.empty else 1
    new_row = pd.DataFrame([{'id': new_id, 'Q': st.session_state.current_q, 'チーム': t_name, '名前': p_name, '項目': item, '詳細': detail, '結果': res, '点数': pts}])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.session_state.mode = "選手選択"; st.toast(f"記録完了")

# --- 4. タブ構成 ---
tab_input, tab_report, tab_edit = st.tabs(["✍️ 記録入力", "📄 レポート", "🛠 修正"])

# --- 【タブ1】記録入力 ---
with tab_input:
    if not st.session_state.history.empty:
        try:
            qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[home_name, away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            qs['Total'] = qs.sum(axis=1); st.table(qs.astype(int))
        except: pass
    st.session_state.current_q = st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")
    st.divider()

    # --- 自チーム選手 (HOME) 5列固定 ---
    st.write(f"🔵 **{home_name}**")
    h_rows = [home_players[i:i + 5] for i in range(0, len(home_players), 5)]
    for row_players in h_rows:
        cols = st.columns(5)
        for i, p_num in enumerate(row_players):
            if cols[i].button(p_num, key=f"h_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': home_name}; st.session_state.mode = "項目選択"; st.rerun()

    if st.button(f"⏰ {home_name} TOUT", use_container_width=True): record("TOUT", team=home_name, name="TEAM")

    # --- 操作パネル ---
    st.divider()
    with st.container(border=True):
        if st.session_state.mode == "選手選択": st.info("選手をタップ")
        elif st.session_state.mode == "項目選択":
            st.subheader(f"#{st.session_state.tmp.get('player')}")
            c = st.columns(3)
            if c[0].button("2P", use_container_width=True, type="primary"): st.session_state.tmp['item']="2P"; st.session_state.mode="エリア選択"; st.rerun()
            if c[1].button("3P", use_container_width=True, type="primary"): st.session_state.tmp['item']="3P"; st.session_state.mode="エリア選択"; st.rerun()
            if c[2].button("FT", use_container_width=True): st.session_state.tmp['item']="FT"; st.session_state.mode="結果選択"; st.rerun()
            o = st.columns(4)
            with o[0]:
                if st.button("OR", use_container_width=True): record("OR"); st.rerun()
                if st.button("DR", use_container_width=True): record("DR"); st.rerun()
            with o[1]:
                if st.button("AST", use_container_width=True): record("AST"); st.rerun()
                if st.button("STL", use_container_width=True): record("STL"); st.rerun()
            with o[2]:
                if st.button("F", use_container_width=True): record("Foul"); st.rerun()
                if st.button("BLK", use_container_width=True): record("BLK"); st.rerun()
            with o[3]:
                if st.button("TV", use_container_width=True): record("TO", "TV"); st.rerun()
                if st.button("DD", use_container_width=True): record("TO", "DD"); st.rerun()
                if st.button("PM", use_container_width=True): record("TO", "PM"); st.rerun()
                if st.button("24S", use_container_width=True): record("TO", "24S"); st.rerun()
            if st.button("キャンセル", use_container_width=True): st.session_state.mode="選手選択"; st.rerun()
        elif st.session_state.mode == "エリア選択":
            it = st.session_state.tmp.get('item', '2P')
            r1, r2, r3 = st.columns(3), st.columns(3), st.columns(5)
            if it == "2P":
                for i, a in enumerate(["左下", "中下", "右下"]):
                    if r1[i].button(a, use_container_width=True): st.session_state.tmp['area']=a; st.session_state.mode="結果選択"; st.rerun()
                for i, a in enumerate(["左レ", "中レ", "右レ"]):
                    if r2[i].button(a, use_container_width=True): st.session_state.tmp['area']=a; st.session_state.mode="結果選択"; st.rerun()
                for i, a in enumerate(["左角", "左45", "中", "右45", "右角"]):
                    if r3[i].button(a, use_container_width=True): st.session_state.tmp['area']=a; st.session_state.mode="結果選択"; st.rerun()
            else:
                r4 = st.columns(5)
                for i, a in enumerate(["左角", "左45", "中", "右45", "右角"]):
                    if r4[i].button(a, use_container_width=True): st.session_state.tmp['area']=a; st.session_state.mode="結果選択"; st.rerun()
            if st.button("戻る"): st.session_state.mode="項目選択"; st.rerun()
        elif st.session_state.mode == "結果選択":
            st.write(f"🎯 {st.session_state.tmp.get('area', 'FT')}")
            sc, fl = st.columns(2)
            pts = {"2P": 2, "3P": 3, "FT": 1}.get(st.session_state.tmp.get('item', '2P'), 0)
            if sc.button("SUCCESS", use_container_width=True, type="primary"): record(st.session_state.tmp.get('item'), detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts); st.rerun()
            if fl.button("MISS", use_container_width=True): record(st.session_state.tmp.get('item'), detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0); st.rerun()
            if st.button("戻る"): st.session_state.mode="エリア選択" if "P" in st.session_state.tmp.get('item','') else "項目選択"; st.rerun()
    st.divider()

    # --- 相手チーム選手 (AWAY) 5列固定 ---
    if st.button(f"⏰ {away_name} TOUT", use_container_width=True): record("TOUT", team=away_name, name="TEAM")
    st.write(f"🔴 **{away_name}**")
    a_rows = [away_players[i:i + 5] for i in range(0, len(away_players), 5)]
    for row_players in a_rows:
        cols = st.columns(5)
        for i, p_num in enumerate(row_players):
            if cols[i].button(p_num, key=f"a_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': away_name}; st.session_state.mode = "項目選択"; st.rerun()

# --- 【タブ2】分析レポート ---
# (V02.6と同じロジックを維持)
with tab_report:
    if st.session_state.history.empty: st.info("データなし")
    else:
        st.title(f"📊 {tournament_name}")
        st.header("1. スコア推移")
        try:
            rep_qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[home_name, away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            rep_qs['Total'] = rep_qs.sum(axis=1); st.table(rep_qs.astype(int))
        except: pass

        st.header("2. 個人スタッツ")
        def build_box(t_name, p_list_source):
            df = st.session_state.history[st.session_state.history['チーム'] == t_name]
            rows = []
            t_pts, t_m2i, t_m2a, t_m3i, t_m3a, t_fti, t_fta = 0,0,0,0,0,0,0
            t_orb, t_drb, t_ast, t_stl, t_foul, t_tv, t_dd, t_pm, t_s24 = 0,0,0,0,0,0,0,0,0
            
            def fmt_stat(m, a):
                return f"{m}/{a} ({(m/a*100):.0f}%)" if a > 0 else f"{m}/{a} (0%)"

            for p_num in p_list_source:
                p_name = f"{p_num}番"; pdf = df[df['名前'] == p_name]
                m2i, m2a = len(pdf[(pdf['項目']=='2P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='2P'])
                m3i, m3a = len(pdf[(pdf['項目']=='3P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='3P'])
                fti, fta = len(pdf[(pdf['項目']=='FT') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='FT'])
                orb, drb = len(pdf[pdf['項目']=='OR']), len(pdf[pdf['項目']=='DR'])
                ast, stl, foul = len(pdf[pdf['項目']=='AST']), len(pdf[pdf['項目']=='STL']), len(pdf[pdf['項目']=='Foul'])
                to_pdf = pdf[pdf['項目']=='TO']
                tv, dd, pm, s24 = len(to_pdf[to_pdf['詳細']=='TV']), len(to_pdf[to_pdf['詳細']=='DD']), len(to_pdf[to_pdf['詳細']=='PM']), len(to_pdf[to_pdf['詳細']=='24S'])
                pts = pdf['点数'].sum()

                t_pts+=pts; t_m2i+=m2i; t_m2a+=m2a; t_m3i+=m3i; t_m3a+=m3a; t_fti+=fti; t_fta+=fta
                t_orb+=orb; t_drb+=drb; t_ast+=ast; t_stl+=stl; t_foul+=foul; t_tv+=tv; t_dd+=dd; t_pm+=pm; t_s24+=s24

                rows.append({
                    '#': p_num, 'Pts': pts,
                    'FG(M/A/%)': fmt_stat(m2i+m3i, m2a+m3a),
                    '3P(M/A/%)': fmt_stat(m3i, m3a),
                    'FT(M/A/%)': fmt_stat(fti, fta),
                    'REB(O/D)': f"{orb+drb} ({orb}/{drb})",
                    'As': ast, 'St': stl, 'F': foul,
                    'TO(T/D/P/2S)': f"{tv+dd+pm+s24} ({tv}/{dd}/{pm}/{s24})"
                })
            
            rows.append({
                '#': 'TOTAL', 'Pts': t_pts,
                'FG(M/A/%)': fmt_stat(t_m2i+t_m3i, t_m2a+t_m3a),
                '3P(M/A/%)': fmt_stat(t_m3i, t_m3a),
                'FT(M/A/%)': fmt_stat(t_fti, t_fta),
                'REB(O/D)': f"{t_orb+t_drb} ({t_orb}/{t_drb})",
                'As': t_ast, 'St': t_stl, 'F': t_foul,
                'TO(T/D/P/2S)': f"{t_tv+t_dd+t_pm+t_s24} ({t_tv}/{t_dd}/{t_pm}/{t_s24})"
            })
            st.write(f"### {t_name}"); st.table(pd.DataFrame(rows).set_index('#'))

        build_box(home_name, home_players); build_box(away_name, away_players)
        st.header("3. 詳細ログ"); st.dataframe(st.session_state.history.iloc[::-1], use_container_width=True)
        csv = st.session_state.history.to_csv(index=False).encode('utf_8_sig')
        st.download_button("📊 CSV保存", csv, f"report.csv", "text/csv")

with tab_edit:
    st.header("🛠 修正")
    if not st.session_state.history.empty:
        for i, row in st.session_state.history.iloc[::-1].iterrows():
            cols = st.columns([4, 1])
            cols[0].write(f"{row['Q']}|{row['名前']}|{row['項目']}({row['詳細']})")
            if cols[1].button("🗑️", key=f"del_{i}"):
                st.session_state.history = st.session_state.history.drop(i); st.rerun()

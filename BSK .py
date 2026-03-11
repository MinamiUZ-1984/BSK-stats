import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="バスケ分析Pro V03.5", layout="centered")

# --- 0. CSS注入 (文字重なり解消・究極スリム設定) ---
st.markdown("""
    <style>
    /* 記録入力のボタン並びを強制 */
    [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 0.2rem !important; }
    [data-testid="stHorizontalBlock"] > div { width: 100% !important; flex: 1 1 0% !important; min-width: 0px !important; }
    .stButton > button { padding: 4px 1px !important; font-size: 11px !important; width: 100% !important; }
    
    /* レポートの表をiPhone幅にねじ込むための極小設定 */
    div[data-testid="stTable"] table { font-size: 8px !important; width: 100% !important; table-layout: fixed; }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td { 
        padding: 1px 0px !important; /* 余白をゼロに */
        text-align: center !important; 
        white-space: pre-wrap !important; 
        line-height: 1.0 !important; /* 行間を極限まで詰める */
        word-break: break-all;
    }
    /* 表の枠線を少し細くしてスッキリさせる */
    table, th, td { border: 0.1px solid #ddd !important; }
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
    away_name = st.text_input("相手チーム名", "AWAY").strip()
    away_players = [n.strip() for n in st.text_area("相手チーム背番号", ",".join([str(i) for i in range(4, 24)])).split(",") if n.strip()]
    st.divider()
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

# --- 【タブ1】記録入力 --- (V02.9~V03.4 構成を維持)
with tab_input:
    if not st.session_state.history.empty:
        try:
            qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[home_name, away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            qs['Total'] = qs.sum(axis=1); st.table(qs.astype(int))
        except: pass
    st.session_state.current_q = st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True)
    st.divider()
    
    # HOME
    st.write(f"🔵 **{home_name}**")
    for i in range(0, len(home_players), 5):
        row_players = home_players[i:i+5]; cols = st.columns(5)
        for idx, p_num in enumerate(row_players):
            if cols[idx].button(p_num, key=f"h_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': home_name}; st.session_state.mode = "項目選択"; st.rerun()
    if st.button(f"⏰ {home_name} TOUT", use_container_width=True): record("TOUT", team=home_name, name="TEAM")

    # 操作パネル
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
            areas = ["左下", "中下", "右下", "左レ", "中レ", "右レ", "左角", "左45", "中", "右45", "右角"]
            for i in range(3):
                if r1[i].button(areas[i], use_container_width=True): st.session_state.tmp['area']=areas[i]; st.session_state.mode="結果選択"; st.rerun()
            for i in range(3):
                if r2[i].button(areas[i+3], use_container_width=True): st.session_state.tmp['area']=areas[i+3]; st.session_state.mode="結果選択"; st.rerun()
            for i in range(5):
                if r3[i].button(areas[i+6], use_container_width=True): st.session_state.tmp['area']=areas[i+6]; st.session_state.mode="結果選択"; st.rerun()
            if st.button("戻る"): st.session_state.mode="項目選択"; st.rerun()
        elif st.session_state.mode == "結果選択":
            st.write(f"🎯 {st.session_state.tmp.get('area', 'FT')}")
            sc = st.columns(2)
            pts = {"2P": 2, "3P": 3, "FT": 1}.get(st.session_state.tmp.get('item', '2P'), 0)
            if sc[0].button("SUCCESS", use_container_width=True, type="primary"): record(st.session_state.tmp.get('item'), detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts); st.rerun()
            if sc[1].button("MISS", use_container_width=True): record(st.session_state.tmp.get('item'), detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0); st.rerun()
            if st.button("戻る"): st.session_state.mode="エリア選択" if "P" in st.session_state.tmp.get('item','') else "項目選択"; st.rerun()

    st.divider()
    st.write(f"🔴 **{away_name}**")
    for i in range(0, len(away_players), 5):
        row_players = away_players[i:i+5]; cols = st.columns(5)
        for idx, p_num in enumerate(row_players):
            if cols[idx].button(p_num, key=f"a_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': away_name}; st.session_state.mode = "項目選択"; st.rerun()

# --- 【タブ2】分析レポート (究極スリム化) ---
with tab_report:
    if st.session_state.history.empty: st.info("データなし")
    else:
        st.header("1. スコア")
        try:
            rep_qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[home_name, away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            rep_qs['Total'] = rep_qs.sum(axis=1); st.table(rep_qs.astype(int))
        except: pass

        st.header("2. 個人統計")
        def get_stats_df(t_name, p_list):
            df = st.session_state.history[st.session_state.history['チーム'] == t_name]
            rows = []
            tp, tm2i, tm2a, tm3i, tm3a, tfi, tfa, tor, tdr, tast, tstl, tblk, tf, ttv, tdd, tpm, ts24 = [0]*17
            def fmt_stat(m, a): return f"{m}/{a}\n{(m/a*100):.0f}%" if a > 0 else "0/0\n0%"

            for p_num in p_list:
                pn = f"{p_num}番"; pdf = df[df['名前'] == pn]
                m2i, m2a = len(pdf[(pdf['項目']=='2P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='2P'])
                m3i, m3a = len(pdf[(pdf['項目']=='3P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='3P'])
                fi, fa = len(pdf[(pdf['項目']=='FT') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='FT'])
                orb, drb = len(pdf[pdf['項目']=='OR']), len(pdf[pdf['項目']=='DR'])
                ast, stl, blk, f = len(pdf[pdf['項目']=='AST']), len(pdf[pdf['項目']=='STL']), len(pdf[pdf['項目']=='BLK']), len(pdf[pdf['項目']=='Foul'])
                to = pdf[pdf['項目']=='TO']
                tv, dd, pm, s24 = len(to[to['詳細']=='TV']), len(to[to['詳細']=='DD']), len(to[to['詳細']=='PM']), len(to[to['詳細']=='24S'])
                p = pdf['点数'].sum()

                tp+=p; tm2i+=m2i; tm2a+=m2a; tm3i+=m3i; tm3a+=m3a; tfi+=fi; tfa+=fa; tor+=orb; tdr+=drb; tast+=ast; tstl+=stl; tblk+=blk; tf+=f; ttv+=tv; tdd+=dd; tpm+=pm; ts24+=s24
                
                rows.append({
                    '#': p_num, 'Pts': p, 
                    'FG\n(M/A)': fmt_stat(m2i+m3i, m2a+m3a), 
                    '3P\n(M/A)': fmt_stat(m3i, m3a), 
                    'FT\n(M/A)': fmt_stat(fi, fa), 
                    'REB\n(D/O)': f"{drb+orb}\n({drb}/{orb})", 
                    'As': ast, 'St': stl, 'B': blk, 'F': f, 
                    'TO\n(T/D/P/2)': f"{tv+dd+pm+s24}\n({tv}/{dd}/{pm}/{s24})"
                })
            
            rows.append({
                '#': 'Total', 'Pts': tp, 
                'FG\n(M/A)': fmt_stat(tm2i+tm3i, tm2a+tm3a), 
                '3P\n(M/A)': fmt_stat(tm3i, tm3a), 
                'FT\n(M/A)': fmt_stat(tfi, tfa), 
                'REB\n(D/O)': f"{tdr+tor}\n({tdr}/{tor})", 
                'As': tast, 'St': tstl, 'B': tblk, 'F': tf, 
                'TO\n(T/D/P/2)': f"{ttv+tdd+tpm+ts24}\n({ttv}/{tdd}/{tpm}/{ts24})"
            })
            return pd.DataFrame(rows)

        h_stats = get_stats_df(home_name, home_players); a_stats = get_stats_df(away_name, away_players)
        st.write(f"🔵 **{home_name}**"); st.table(h_stats.set_index('#'))
        st.write(f"🔴 **{away_name}**"); st.table(a_stats.set_index('#'))

        csv_stats = pd.concat([h_stats, a_stats], ignore_index=True).to_csv(index=False).encode('utf_8_sig')
        st.download_button("📊 統計CSV保存", csv_stats, f"{tournament_name}_stats.csv", "text/csv")

with tab_edit:
    st.header("🛠 修正")
    if not st.session_state.history.empty:
        for i, row in st.session_state.history.iloc[::-1].iterrows():
            cols = st.columns([4, 1])
            cols[0].write(f"{row['Q']}|{row['名前']}|{row['項目']}({row['詳細']})")
            if cols[1].button("🗑️", key=f"del_{i}"):
                st.session_state.history = st.session_state.history.drop(i); st.rerun()

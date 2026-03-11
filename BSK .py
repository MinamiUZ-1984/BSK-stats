import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="バスケ分析Pro V04.3", layout="centered")

# --- 0. CSS注入 (V04.2準拠：タブ保護 & 3列グリッド) ---
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    [data-testid="stHorizontalBlock"] { 
        flex-direction: row !important; 
        flex-wrap: nowrap !important; 
        gap: 0.3rem !important; 
    }
    [data-testid="stHorizontalBlock"] > div { 
        width: 100% !important; 
        flex: 1 1 0% !important; 
        min-width: 0px !important; 
    }
    .stButton > button { 
        padding: 5px 2px !important; 
        font-size: 13px !important; 
        width: 100% !important; 
        font-weight: bold;
        min-height: 40px !important;
    }
    div[data-testid="stTable"] table { font-size: 9px !important; width: 100% !important; table-layout: fixed; }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td { 
        padding: 2px 1px !important; text-align: center !important; 
        white-space: pre-wrap !important; line-height: 1.1 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. データ初期化 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state: st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state: st.session_state.tmp = {}
if 'current_q' not in st.session_state: st.session_state.current_q = "1Q"

# --- 2. サイドバー (設定維持) ---
with st.sidebar:
    st.header("🏆 試合設定")
    tournament_name = st.text_input("大会名", "練習試合")
    game_date = st.date_input("試合日")
    st.divider()
    home_name = st.text_input("自チーム名", "HOME").strip()
    all_h = [n.strip() for n in st.text_area("自チーム背番号(全)", "4,5,6,7,8,9,10,11,12,13,14,15").split(",") if n.strip()]
    active_h = st.multiselect(f"🔵 {home_name} オンコート", all_h, default=all_h[:5])
    st.divider()
    away_name = st.text_input("相手チーム名", "AWAY").strip()
    all_a = [n.strip() for n in st.text_area("相手チーム背番号(全)", "4,5,6,7,8,9,10,11,12,13,14,15").split(",") if n.strip()]
    active_a = st.multiselect(f"🔴 {away_name} オンコート", all_a, default=all_a[:5])
    if st.button("全リセット"):
        st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
        st.rerun()

# --- 3. 共通記録関数 ---
def record(item, detail="-", res="成功", pts=0, team=None, name=None):
    t_name = team if team else st.session_state.tmp.get('team', 'UNKNOWN')
    p_name = name if name else (f"{st.session_state.tmp['player']}番" if 'player' in st.session_state.tmp else "TEAM")
    new_id = st.session_state.history['id'].max() + 1 if not st.session_state.history.empty else 1
    new_row = pd.DataFrame([{'id': new_id, 'Q': st.session_state.current_q, 'チーム': t_name, '名前': p_name, '項目': item, '詳細': detail, '結果': res, '点数': pts}])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.session_state.mode = "選手選択"; st.toast(f"記録完了")

# --- 4. メインタブ ---
tab_input, tab_report, tab_edit = st.tabs(["✍️ 記録入力", "📄 レポート", "🛠 修正"])

with tab_input:
    if not st.session_state.history.empty:
        try:
            qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[home_name, away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            qs['Total'] = qs.sum(axis=1); st.table(qs.astype(int))
        except: pass
    st.session_state.current_q = st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")

    # オンコート選手 (HOME)
    st.write(f"🔵 **{home_name}**")
    if active_h:
        cols_h = st.columns(len(active_h))
        for i, p_num in enumerate(active_h):
            if cols_h[i].button(p_num, key=f"h_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': home_name}; st.session_state.mode = "項目選択"; st.rerun()

    # アクションパネル
    with st.container(border=True):
        if st.session_state.mode == "選手選択": st.info("選手をタップ")
        elif st.session_state.mode == "項目選択":
            st.write(f"**#{st.session_state.tmp.get('player')}** 項目選択")
            r1 = st.columns(3)
            if r1[0].button("2P", type="primary"): st.session_state.tmp['item']="2P"; st.session_state.mode="エリア選択"; st.rerun()
            if r1[1].button("3P", type="primary"): st.session_state.tmp['item']="3P"; st.session_state.mode="エリア選択"; st.rerun()
            if r1[2].button("FT"): st.session_state.tmp['item']="FT"; st.session_state.mode="結果選択"; st.rerun()
            r2 = st.columns(3)
            if r2[0].button("OR"): record("OR"); st.rerun()
            if r2[1].button("DR"): record("DR"); st.rerun()
            if r2[2].button("AST"): record("AST"); st.rerun()
            r3 = st.columns(3)
            if r3[0].button("STL"): record("STL"); st.rerun()
            if r3[1].button("BLK"): record("BLK"); st.rerun()
            if r3[2].button("F"): record("Foul"); st.rerun()
            st.write("▼ TO")
            r4 = st.columns(4)
            for i, v in enumerate(["TV", "DD", "PM", "24S"]):
                if r4[i].button(v): record("TO", v); st.rerun()
            if st.button("キャンセル", use_container_width=True): st.session_state.mode="選手選択"; st.rerun()
        
        elif st.session_state.mode == "エリア選択":
            it = st.session_state.tmp.get('item', '2P')
            st.write(f"🎯 {it} エリア")
            
            # --- ここでボタンの出し分け ---
            if it == "2P":
                areas_short = ["左下", "中下", "右下"]
                areas_layup = ["左レ", "中レ", "右レ"]
                areas_mid = ["左角", "左45", "中", "右45", "右角"]
                
                a1, a2, a3 = st.columns(3), st.columns(3), st.columns(5)
                for i in range(3):
                    if a1[i].button(areas_short[i]): st.session_state.tmp['area']=areas_short[i]; st.session_state.mode="結果選択"; st.rerun()
                for i in range(3):
                    if a2[i].button(areas_layup[i]): st.session_state.tmp['area']=areas_layup[i]; st.session_state.mode="結果選択"; st.rerun()
                for i in range(5):
                    if a3[i].button(areas_mid[i]): st.session_state.tmp['area']=areas_mid[i]; st.session_state.mode="結果選択"; st.rerun()
            else: # 3P
                areas_long = ["左角", "左45", "中", "右45", "右角"]
                a_long = st.columns(5)
                for i in range(5):
                    if a_long[i].button(areas_long[i]): st.session_state.tmp['area']=areas_long[i]; st.session_state.mode="結果選択"; st.rerun()
            
            if st.button("戻る"): st.session_state.mode="項目選択"; st.rerun()
            
        elif st.session_state.mode == "結果選択":
            st.write(f"🎯 {st.session_state.tmp.get('area', 'FT')}")
            res_c = st.columns(2)
            pts = {"2P": 2, "3P": 3, "FT": 1}.get(st.session_state.tmp.get('item', '2P'), 0)
            if res_c[0].button("SUCCESS", type="primary"): record(st.session_state.tmp.get('item'), detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts); st.rerun()
            if res_c[1].button("MISS"): record(st.session_state.tmp.get('item'), detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0); st.rerun()
            if st.button("戻る"): st.session_state.mode="エリア選択" if "P" in st.session_state.tmp.get('item','') else "項目選択"; st.rerun()

    if st.button(f"⏰ {away_name} TOUT", use_container_width=True): record("TOUT", team=away_name, name="TEAM")
    st.write(f"🔴 **{away_name}**")
    if active_a:
        cols_a = st.columns(len(active_a))
        for i, p_num in enumerate(active_a):
            if cols_a[i].button(p_num, key=f"a_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': away_name}; st.session_state.mode = "項目選択"; st.rerun()

# --- 【タブ2】レポート (V04.2を継承) ---
with tab_report:
    if st.session_state.history.empty: st.info("データなし")
    else:
        st.header("1. スコア推移")
        try:
            rep_qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[home_name, away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            rep_qs['Total'] = rep_qs.sum(axis=1); st.table(rep_qs.astype(int))
        except: pass
        st.header("2. 個人スタッツ")
        def get_stats_df(t_name, p_list_all):
            df = st.session_state.history[st.session_state.history['チーム'] == t_name]
            rows = []
            tp, tm2i, tm2a, tm3i, tm3a, tfi, tfa, tor, tdr, tast, tstl, tblk, tf, ttv, tdd, tpm, ts24 = [0]*17
            def fmt_stat(m, a): return f"{m}/{a}\n{(m/a*100):.0f}%" if a > 0 else "0/0\n0%"
            for p_num in p_list_all:
                pn = f"{p_num}番"; pdf = df[df['名前'] == pn]
                m2i, m2a = len(pdf[(pdf['項目']=='2P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='2P'])
                m3i, m3a = len(pdf[(pdf['項目']=='3P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='3P'])
                fi, fa = len(pdf[(pdf['項目']=='FT') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='FT'])
                orb, drb = len(pdf[pdf['項目']=='OR']), len(pdf[pdf['項目']=='DR'])
                ast, stl, blk, f = len(pdf[pdf['項目']=='AST']), len(pdf[pdf['項目']=='STL']), len(pdf[pdf['項目']=='BLK']), len(pdf[pdf['項目']=='Foul'])
                to = pdf[pdf['項目']=='TO']; tv, dd, pm, s24 = len(to[to['詳細']=='TV']), len(to[to['詳細']=='DD']), len(to[to['詳細']=='PM']), len(to[to['詳細']=='24S'])
                p = pdf['点数'].sum()
                tp+=p; tm2i+=m2i; tm2a+=m2a; tm3i+=m3i; tm3a+=m3a; tfi+=fi; tfa+=fa; tor+=orb; tdr+=drb; tast+=ast; tstl+=stl; tf+=f; ttv+=tv; tdd+=dd; tpm+=pm; ts24+=s24
                rows.append({'#': p_num, 'Pts': p, 'FG\n(M/A)': fmt_stat(m2i+m3i, m2a+m3a), '3P\n(M/A)': fmt_stat(m3i, m3a), 'FT\n(M/A)': fmt_stat(fi, fa), 
                             'REB\n(D/O)': f"{drb+orb}\n({drb}/{orb})", 'As': ast, 'St': stl, 'B': blk, 'F': f, 'TO\n(T/D/P/2)': f"{tv+dd+pm+s24}\n({tv}/{dd}/{pm}/{s24})", 'Team': t_name})
            rows.append({'#': 'Total', 'Pts': tp, 'FG\n(M/A)': fmt_stat(tm2i+tm3i, tm2a+tm3a), '3P\n(M/A)': fmt_stat(tm3i, tm3a), 'FT\n(M/A)': fmt_stat(tfi, tfa), 
                         'REB\n(D/O)': f"{tdr+tor}\n({tdr}/{tor})", 'As': tast, 'St': tstl, 'B': tblk, 'F': tf, 'TO\n(T/D/P/2)': f"{ttv+tdd+tpm+ts24}\n({ttv}/{tdd}/{tpm}/{ts24})", 'Team': t_name})
            return pd.DataFrame(rows)
        st.write(f"🔵 **{home_name}**"); h_df = get_stats_df(home_name, all_h); st.table(h_df.drop(columns='Team').set_index('#'))
        st.write(f"🔴 **{away_name}**"); a_df = get_stats_df(away_name, all_a); st.table(a_df.drop(columns='Team').set_index('#'))
        st.header("3. 詳細ログ"); st.dataframe(st.session_state.history.iloc[::-1], use_container_width=True)
        csv_stats = pd.concat([h_df, a_df], ignore_index=True).to_csv(index=False).encode('utf_8_sig')
        st.download_button("📊 統計CSV", csv_stats, "stats.csv", "text/csv")

with tab_edit:
    st.header("🛠 修正")
    if not st.session_state.history.empty:
        for i, row in st.session_state.history.iloc[::-1].iterrows():
            cols = st.columns([4, 1])
            cols[0].write(f"{row['Q']}|{row['名前']}|{row['項目']}({row['詳細']})")
            if cols[1].button("🗑️", key=f"del_{i}"):
                st.session_state.history = st.session_state.history.drop(i); st.rerun()

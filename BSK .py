import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="バスケ分析Pro V06.0", layout="centered")

# --- 0. CSS注入 (V05系継承) ---
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    [data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; width: 100% !important; gap: 4px !important; }
    [data-testid="stHorizontalBlock"] > div { flex: 1 1 0% !important; min-width: 0 !important; }
    .stButton > button { width: 100% !important; padding: 6px 2px !important; font-size: 13px !important; font-weight: bold !important; min-height: 44px !important; margin-bottom: -10px !important; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    div[data-testid="stTable"] table { font-size: 9px !important; width: 100% !important; }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td { padding: 2px 1px !important; line-height: 1.1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 1. データ初期化 ---
if 'history' not in st.session_state: st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state: st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state: st.session_state.tmp = {}
if 'current_q' not in st.session_state: st.session_state.current_q = "1Q"

# ★新規：ロスターとオンコート状態の保存用
if 'r_str_h' not in st.session_state: st.session_state.r_str_h = "4,5,6,7,8"
if 'act_h' not in st.session_state: st.session_state.act_h = ["4","5","6","7","8"]
if 'r_str_a' not in st.session_state: st.session_state.r_str_a = "4,5,6,7,8"
if 'act_a' not in st.session_state: st.session_state.act_a = ["4","5","6","7","8"]

# --- 2. サイドバー (クイック追加機能搭載) ---
with st.sidebar:
    st.header("🏆 試合設定")
    tournament_name = st.text_input("大会名", "練習試合")
    st.divider()
    
    # === HOME ===
    home_name = st.text_input("自チーム名", "HOME").strip()
    
    # クイック追加UI
    st.write("▼ 新しい選手をコートに追加")
    ch1, ch2 = st.columns([3, 4])
    new_h = ch1.text_input("追加", placeholder="例: 14", label_visibility="collapsed")
    
    with st.expander(f"👥 {home_name} メンバー名簿を手動編集"):
        st.session_state.r_str_h = st.text_area("全背番号 (カンマ区切り)", st.session_state.r_str_h)
    all_h = [n.strip() for n in st.session_state.r_str_h.split(",") if n.strip()]

    if ch2.button("＋追加＆出場", key="add_h"):
        if new_h:
            nums = [x.strip() for x in new_h.split(",") if x.strip()]
            for n in nums:
                if n not in all_h: all_h.append(n)
                if n not in st.session_state.act_h: st.session_state.act_h.append(n)
            st.session_state.r_str_h = ",".join(all_h)
            st.rerun()

    valid_act_h = [x for x in st.session_state.act_h if x in all_h]
    st.session_state.act_h = st.multiselect(f"🔵 {home_name} オンコート", all_h, default=valid_act_h)
    active_h = st.session_state.act_h
    
    st.divider()
    
    # === AWAY ===
    away_name = st.text_input("相手チーム名", "AWAY").strip()
    
    st.write("▼ 新しい選手をコートに追加")
    ca1, ca2 = st.columns([3, 4])
    new_a = ca1.text_input("追加", placeholder="例: 14", label_visibility="collapsed", key="in_a")
    
    with st.expander(f"👥 {away_name} メンバー名簿を手動編集"):
        st.session_state.r_str_a = st.text_area("全背番号 (カンマ区切り)", st.session_state.r_str_a, key="ta_a")
    all_a = [n.strip() for n in st.session_state.r_str_a.split(",") if n.strip()]

    if ca2.button("＋追加＆出場", key="add_a"):
        if new_a:
            nums = [x.strip() for x in new_a.split(",") if x.strip()]
            for n in nums:
                if n not in all_a: all_a.append(n)
                if n not in st.session_state.act_a: st.session_state.act_a.append(n)
            st.session_state.r_str_a = ",".join(all_a)
            st.rerun()

    valid_act_a = [x for x in st.session_state.act_a if x in all_a]
    st.session_state.act_a = st.multiselect(f"🔴 {away_name} オンコート", all_a, default=valid_act_a)
    active_a = st.session_state.act_a
    
    st.divider()
    if st.button("全データリセット", type="secondary"):
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

# --- 4. メイン画面 ---
tab_input, tab_report, tab_edit = st.tabs(["✍️ 記録入力", "📄 統計レポート", "🛠 修正"])

with tab_input:
    if not st.session_state.history.empty:
        try:
            qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[home_name, away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            qs['Total'] = qs.sum(axis=1); st.table(qs.astype(int))
        except: pass
    st.session_state.current_q = st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")

    # HOME
    st.write(f"🔵 **{home_name}**")
    if not active_h: st.warning("サイドバーで選手を選んでください")
    else:
        cols_h = st.columns(len(active_h))
        for i, p_num in enumerate(active_h):
            if cols_h[i].button(p_num, key=f"h_{p_num}"):
                st.session_state.tmp = {'player': p_num, 'team': home_name}; st.session_state.mode = "項目選択"; st.rerun()

    # アクションパネル
    with st.container(border=True):
        if st.session_state.mode == "選手選択": 
            st.info("選手をタップしてください")
        elif st.session_state.mode == "項目選択":
            st.write(f"**#{st.session_state.tmp.get('player')}** 項目選択")
            r1 = st.columns(3)
            r1[0].button("2P", type="primary", on_click=lambda: (st.session_state.update({"mode": "エリア選択"}), st.session_state.tmp.update({"item": "2P"})))
            r1[1].button("3P", type="primary", on_click=lambda: (st.session_state.update({"mode": "エリア選択"}), st.session_state.tmp.update({"item": "3P"})))
            r1[2].button("FT", on_click=lambda: (st.session_state.update({"mode": "結果選択"}), st.session_state.tmp.update({"item": "FT"})))
            
            r2 = st.columns(3)
            r2[0].button("OR", on_click=lambda: record("OR"))
            r2[1].button("DR", on_click=lambda: record("DR"))
            r2[2].button("AST", on_click=lambda: record("AST"))
            
            r3 = st.columns(3)
            r3[0].button("STL", on_click=lambda: record("STL"))
            r3[1].button("BLK", on_click=lambda: record("BLK"))
            r3[2].button("F", on_click=lambda: record("Foul"))
            
            st.write("▼ TurnOver")
            r4 = st.columns(4)
            r4[0].button("TV", on_click=lambda: record("TO", "TV"))
            r4[1].button("DD", on_click=lambda: record("TO", "DD"))
            r4[2].button("PM", on_click=lambda: record("TO", "PM"))
            r4[3].button("24S", on_click=lambda: record("TO", "24S"))
            
            st.button("キャンセル", on_click=lambda: st.session_state.update({"mode": "選手選択"}))
            
        elif st.session_state.mode == "エリア選択":
            it = st.session_state.tmp.get('item', '2P')
            st.write(f"🎯 {it} エリア")
            if it == "2P":
                areas_short = ["左下", "中下", "右下"]; areas_layup = ["左レ", "中レ", "右レ"]; areas_mid = ["左角", "左45", "中", "右45", "右角"]
                a1, a2, a3 = st.columns(3), st.columns(3), st.columns(5)
                for i in range(3): a1[i].button(areas_short[i], on_click=lambda a=areas_short[i]: (st.session_state.tmp.update({"area": a}), st.session_state.update({"mode": "結果選択"})))
                for i in range(3): a2[i].button(areas_layup[i], on_click=lambda a=areas_layup[i]: (st.session_state.tmp.update({"area": a}), st.session_state.update({"mode": "結果選択"})))
                for i in range(5): a3[i].button(areas_mid[i], on_click=lambda a=areas_mid[i]: (st.session_state.tmp.update({"area": a}), st.session_state.update({"mode": "結果選択"})))
            else:
                areas_long = ["左角", "左45", "中", "右45", "右角"]
                a_long_1 = st.columns(3); a_long_2 = st.columns(3)
                a_long_1[0].button("左角", on_click=lambda: (st.session_state.tmp.update({"area": "左角"}), st.session_state.update({"mode": "結果選択"})))
                a_long_1[1].button("左45", on_click=lambda: (st.session_state.tmp.update({"area": "左45"}), st.session_state.update({"mode": "結果選択"})))
                a_long_1[2].button("中", on_click=lambda: (st.session_state.tmp.update({"area": "中"}), st.session_state.update({"mode": "結果選択"})))
                a_long_2[0].button("右45", on_click=lambda: (st.session_state.tmp.update({"area": "右45"}), st.session_state.update({"mode": "結果選択"})))
                a_long_2[1].button("右角", on_click=lambda: (st.session_state.tmp.update({"area": "右角"}), st.session_state.update({"mode": "結果選択"})))

            st.button("戻る", on_click=lambda: st.session_state.update({"mode": "項目選択"}))
            
        elif st.session_state.mode == "結果選択":
            st.write(f"🎯 {st.session_state.tmp.get('area', 'FT')}")
            sc = st.columns(2)
            item = st.session_state.tmp.get('item', '2P')
            pts = {"2P": 2, "3P": 3, "FT": 1}.get(item, 0)
            
            def handle_success():
                record(item, detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts)
                st.session_state.mode = "アシスト選択" if item in ["2P", "3P"] else "選手選択"
                
            sc[0].button("SUCCESS", type="primary", on_click=handle_success)
            sc[1].button("MISS", on_click=lambda: record(item, detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0))
            st.button("戻る", on_click=lambda: st.session_state.update({"mode": "エリア選択" if "P" in item else "項目選択"}))

        elif st.session_state.mode == "アシスト選択":
            scorer = st.session_state.tmp.get('player')
            t_name = st.session_state.tmp.get('team')
            st.write(f"🏀 **#{scorer}** 得点！アシストは？")
            
            active_list = active_h if t_name == home_name else active_a
            assist_candidates = [p for p in active_list if p != scorer]
            
            if assist_candidates:
                ast_c = st.columns(len(assist_candidates))
                for i, p_num in enumerate(assist_candidates):
                    ast_c[i].button(p_num, key=f"ast_{p_num}", on_click=lambda p=p_num: record("AST", detail=f"to #{scorer}", res="成功", pts=0, team=t_name, name=f"{p}番"))
            
            st.write("---")
            st.button("❌ アシストなし", on_click=lambda: st.session_state.update({"mode": "選手選択"}))

    if st.button(f"⏰ {away_name} TOUT"): record("TOUT", team=away_name, name="TEAM")
    st.write(f"🔴 **{away_name}**")
    if active_a:
        cols_a = st.columns(len(active_a))
        for i, p_num in enumerate(active_a):
            if cols_a[i].button(p_num, key=f"a_{p_num}"):
                st.session_state.tmp = {'player': p_num, 'team': away_name}; st.session_state.mode = "項目選択"; st.rerun()

# --- レポートタブ ---
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
                tp+=p; tm2i+=m2i; tm2a+=m2a; tm3i+=m3i; tm3a+=m3a; tfi+=fi; tfa+=fa; tor+=orb; tdr+=drb; tast+=ast; tstl+=stl; tblk+=blk; tf+=f; ttv+=tv; tdd+=dd; tpm+=pm; ts24+=s24
                rows.append({'#': p_num, 'Pts': p, 'FG\n(M/A)': fmt_stat(m2i+m3i, m2a+m3a), '3P\n(M/A)': fmt_stat(m3i, m3a), 'FT\n(M/A)': fmt_stat(fi, fa), 
                             'REB\n(D/O)': f"{drb+orb}\n({drb}/{orb})", 'As': ast, 'St': stl, 'B': blk, 'F': f, 'TO\n(T/D/P/2)': f"{tv+dd+pm+s24}\n({tv}/{dd}/{pm}/{s24})", 'Team': t_name})
            rows.append({'#': 'Total', 'Pts': tp, 'FG\n(M/A)': fmt_stat(tm2i+tm3i, tm2a+tm3a), '3P\n(M/A)': fmt_stat(tm3i, tm3a), 'FT\n(M/A)': fmt_stat(tfi, tfa), 
                         'REB\n(D/O)': f"{tdr+tor}\n({tdr}/{tor})", 'As': tast, 'St': tstl, 'B': tblk, 'F': tf, 'TO\n(T/D/P/2)': f"{ttv+tdd+tpm+ts24}\n({ttv}/{tdd}/{tpm}/{ts24})", 'Team': t_name})
            return pd.DataFrame(rows)
        
        h_df = get_stats_df(home_name, all_h); st.table(h_df.drop(columns='Team').set_index('#'))
        a_df = get_stats_df(away_name, all_a); st.table(a_df.drop(columns='Team').set_index('#'))

        st.divider()
        st.header("3. 詳細ログ")
        st.dataframe(st.session_state.history.iloc[::-1], use_container_width=True)
        
        csv_stats = pd.concat([h_df, a_df], ignore_index=True).to_csv(index=False).encode('utf_8_sig')
        st.download_button("📊 統計CSV", csv_stats, "stats.csv", "text/csv")
        csv_log = st.session_state.history.to_csv(index=False).encode('utf_8_sig')
        st.download_button("📜 ログCSV", csv_log, "log.csv", "text/csv")

with tab_edit:
    st.header("🛠 修正")
    if not st.session_state.history.empty:
        for i, row in st.session_state.history.iloc[::-1].iterrows():
            cols = st.columns([4, 1])
            cols[0].write(f"{row['Q']}|{row['名前']}|{row['項目']}({row['詳細']})")
            if cols[1].button("🗑️", key=f"del_{i}"):
                st.session_state.history = st.session_state.history.drop(i); st.rerun()

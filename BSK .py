import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="バスケ分析Pro", layout="centered")

# --- 1. データ初期化 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state: st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state: st.session_state.tmp = {}
if 'current_q' not in st.session_state: st.session_state.current_q = "1Q"
if 'memo' not in st.session_state: st.session_state.memo = ""

# --- 2. サイドバー：詳細設定 ---
with st.sidebar:
    st.header("🏆 試合・チーム設定")
    tournament_name = st.text_input("大会名", "練習試合")
    game_date = st.date_input("試合日")
    st.divider()
    home_name = st.text_input("自チーム名", "HOME").strip()
    home_players_input = st.text_area("自チーム背番号", ",".join([str(i) for i in range(4, 24)]))
    home_players = [n.strip() for n in home_players_input.split(",") if n.strip()]
    st.divider()
    away_name = st.text_input("相手チーム名", "AWAY").strip()
    away_players_input = st.text_area("相手チーム背番号", ",".join([str(i) for i in range(4, 24)]))
    away_players = [n.strip() for n in away_players_input.split(",") if n.strip()]
    st.divider()
    st.session_state.memo = st.text_area("📝 コーチメモ", st.session_state.memo)

    if st.button("全データをリセット", type="secondary"):
        st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
        st.session_state.mode = "選手選択"
        st.rerun()

# --- 3. 共通記録関数 ---
def record(item, name=None, team=None, detail="-", res="成功", pts=0):
    p_name = name if name else (f"{st.session_state.tmp['player']}番" if 'player' in st.session_state.tmp else "TEAM")
    t_name = team if team else (st.session_state.tmp['team'] if 'team' in st.session_state.tmp else "UNKNOWN")
    
    new_id = st.session_state.history['id'].max() + 1 if not st.session_state.history.empty else 1
    new_row = pd.DataFrame([{
        'id': new_id, 'Q': st.session_state.current_q, 'チーム': t_name, '名前': p_name, 
        '項目': item, '詳細': detail, '結果': res, '点数': pts
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.session_state.mode = "選手選択"
    st.toast(f"{t_name} {p_name} {item} 記録")

# --- 4. メインタブ構成 ---
tab_input, tab_report, tab_edit = st.tabs(["✍️ 記録入力", "📄 分析レポート", "🛠 修正・削除"])

# --- 【タブ1】記録入力画面 ---
with tab_input:
    # リアルタイム簡易スコア
    if not st.session_state.history.empty:
        try:
            qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0)
            qs = qs.reindex(index=[home_name, away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            qs['Total'] = qs.sum(axis=1)
            st.table(qs.astype(int))
        except: pass

    st.session_state.current_q = st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")
    st.divider()

    # --- HOME Section ---
    st.write(f"🔵 **{home_name}**")
    h_cols = st.columns(5)
    for i, p_num in enumerate(home_players):
        if h_cols[i % 5].button(p_num, key=f"h_{p_num}", use_container_width=True):
            st.session_state.tmp = {'player': p_num, 'team': home_name}; st.session_state.mode = "項目選択"
    
    # HOME クイックボタン (選手番号の下)
    hq1, hq2, hq3 = st.columns(3)
    if hq1.button("🚫 HOME BLK", key="hq_blk", use_container_width=True): record("BLK", team=home_name)
    if hq2.button("⚠️ HOME VIOL", key="hq_viol", use_container_width=True): record("VIOL", team=home_name)
    if hq3.button("⏰ HOME TOUT", key="hq_tout", use_container_width=True): record("TOUT", team=home_name)

    # --- 操作パネル (MIDDLE) ---
    st.divider()
    with st.container(border=True):
        if st.session_state.mode == "選手選択":
            st.info("選手またはクイックボタンをタップしてください")
        elif st.session_state.mode == "項目選択":
            st.subheader(f"⚡ {st.session_state.tmp.get('team')} #{st.session_state.tmp.get('player')}")
            c = st.columns(3)
            if c[0].button("2P", use_container_width=True, type="primary"): st.session_state.tmp['item']="2P"; st.session_state.mode="エリア選択"; st.rerun()
            if c[1].button("3P", use_container_width=True, type="primary"): st.session_state.tmp['item']="3P"; st.session_state.mode="エリア選択"; st.rerun()
            if c[2].button("FT", use_container_width=True): st.session_state.tmp['item']="FT"; st.session_state.mode="結果選択"; st.rerun()
            
            o = st.columns(4)
            if o[0].button("OR", use_container_width=True): record("OR"); st.rerun()
            if o[0].button("DR", use_container_width=True): record("DR"); st.rerun()
            if o[1].button("AST", use_container_width=True): record("AST"); st.rerun()
            if o[1].button("STL", use_container_width=True): record("STL"); st.rerun()
            if o[2].button("F", use_container_width=True): record("Foul"); st.rerun()
            if o[2].button("BLK", use_container_width=True): record("BLK"); st.rerun()
            if o[3].button("TV", use_container_width=True): record("TO", "TV"); st.rerun()
            if o[3].button("DD", use_container_width=True): record("TO", "DD"); st.rerun()
            if o[3].button("PM", use_container_width=True): record("TO", "PM"); st.rerun()
            if st.button("キャンセル", use_container_width=True): st.session_state.mode="選手選択"; st.rerun()

        elif st.session_state.mode == "エリア選択":
            it = st.session_state.tmp.get('item', '2P')
            if it == "2P":
                r1, r2, r3 = st.columns(3), st.columns(3), st.columns(5)
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
            pts = {"2P": 2, "3P": 3, "FT": 1}.get(st.session_state.tmp.get('item', '2P'), 0)
            if sc.button("SUCCESS", use_container_width=True, type="primary"): record(st.session_state.tmp.get('item'), detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts); st.rerun()
            if fl.button("MISS", use_container_width=True): record(st.session_state.tmp.get('item'), detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0); st.rerun()
            if st.button("戻る"): st.session_state.mode="エリア選択" if "P" in st.session_state.tmp.get('item','') else "項目選択"; st.rerun()

    st.divider()

    # --- AWAY Section ---
    # AWAY クイックボタン (選手番号の上)
    aq1, aq2, aq3 = st.columns(3)
    if aq1.button("🚫 AWAY BLK", key="aq_blk", use_container_width=True): record("BLK", team=away_name)
    if aq2.button("⚠️ AWAY VIOL", key="aq_viol", use_container_width=True): record("VIOL", team=away_name)
    if aq3.button("⏰ AWAY TOUT", key="aq_tout", use_container_width=True): record("TOUT", team=away_name)
    
    st.write(f"🔴 **{away_name}**")
    a_cols = st.columns(5)
    for i, p_num in enumerate(away_players):
        if a_cols[i % 5].button(p_num, key=f"a_{p_num}", use_container_width=True):
            st.session_state.tmp = {'player': p_num, 'team': away_name}; st.session_state.mode = "項目選択"

# --- 【タブ2】分析レポート ---
with tab_report:
    if st.session_state.history.empty:
        st.info("データなし")
    else:
        st.title(f"📊 {tournament_name} 分析")
        
        # スコア・タイムアウト集計
        tout_h = len(st.session_state.history[(st.session_state.history['チーム']==home_name) & (st.session_state.history['項目']=='TOUT')])
        tout_a = len(st.session_state.history[(st.session_state.history['チーム']==away_name) & (st.session_state.history['項目']=='TOUT')])
        
        c1, c2 = st.columns(2)
        c1.metric(f"{home_name} タイムアウト", f"{tout_h} 回")
        c2.metric(f"{away_name} タイムアウト", f"{tout_a} 回")

        # 個人ボックススコア
        def build_box(t_name, p_list_source):
            df = st.session_state.history[st.session_state.history['チーム'] == t_name]
            rows = []
            for p_num in p_list_source:
                p_name = f"{p_num}番"
                pdf = df[df['名前'] == p_name]
                m2in, m2at = len(pdf[(pdf['項目']=='2P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='2P'])
                m3in, m3at = len(pdf[(pdf['項目']=='3P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='3P'])
                ftin, ftat = len(pdf[(pdf['項目']=='FT') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='FT'])
                orb, drb = len(pdf[pdf['項目']=='OR']), len(pdf[pdf['項目']=='DR'])
                to_all = pdf[pdf['項目']=='TO']
                viol = len(pdf[pdf['項目']=='VIOL'])
                
                rows.append({
                    'No.': p_name, 'PTS': pdf['点数'].sum(), 'FG': f"{m2in+m3in}-{m2at+m3at}", '3P': f"{m3in}-{m3at}", 
                    'OR': orb, 'DR': drb, 'REB': orb+drb, 'AST': len(pdf[pdf['項目']=='AST']), 
                    'STL': len(pdf[pdf['項目']=='STL']), 'BLK': len(pdf[pdf['項目']=='BLK']), 'F': len(pdf[pdf['項目']=='Foul']),
                    'TO計': len(to_all) + viol, 'TV': len(to_all[to_all['詳細']=='TV']), 'DD': len(to_all[to_all['詳細']=='DD']), 
                    'PM': len(to_all[to_all['詳細']=='PM']), 'VIOL': viol
                })
            st.write(f"### {t_name}")
            st.dataframe(pd.DataFrame(rows).set_index('No.'), use_container_width=True)

        build_box(home_name, home_players)
        build_box(away_name, away_players)
        
        st.header("詳細ログ")
        st.dataframe(st.session_state.history.iloc[::-1], use_container_width=True)

# --- 【タブ3】記録修正 ---
with tab_edit:
    st.header("🛠 修正・削除")
    if not st.session_state.history.empty:
        for i, row in st.session_state.history.iloc[::-1].iterrows():
            cols = st.columns([1, 4, 1])
            cols[0].write(f"#{row.get('id', i)}")
            cols[1].write(f"{row['Q']} | {row['チーム']} {row['名前']} | {row['項目']}({row['詳細']})")
            if cols[2].button("🗑️", key=f"del_{row.get('id', i)}"):
                st.session_state.history = st.session_state.history.drop(i); st.rerun()

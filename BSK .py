import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="バスケ分析Pro V06.1", layout="centered")

# --- 0. CSS注入 (V05.0継承) ---
st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 0.3rem !important; }
    [data-testid="stHorizontalBlock"] > div { width: 100% !important; flex: 1 1 0% !important; min-width: 0px !important; }
    .stButton > button { padding: 5px 2px !important; font-size: 13px !important; width: 100% !important; font-weight: bold;}
    
    div[data-testid="stTable"] table { font-size: 9px !important; width: 100% !important; table-layout: fixed; }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td { 
        padding: 2px 1px !important; text-align: center !important; 
        white-space: pre-wrap !important; line-height: 1.1 !important;
        word-break: break-all;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. データ初期化 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state: st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state: st.session_state.tmp = {}
if 'current_q' not in st.session_state: st.session_state.current_q = "1Q"

# ★新規：ロスターとオンコート状態の保存用
if 'r_str_h' not in st.session_state: st.session_state.r_str_h = "4,5,6,7,8,9,10,11,12,13,14,15"
if 'act_h' not in st.session_state: st.session_state.act_h = ["4","5","6","7","8"]
if 'r_str_a' not in st.session_state: st.session_state.r_str_a = "4,5,6,7,8,9,10,11,12,13,14,15"
if 'act_a' not in st.session_state: st.session_state.act_a = ["4","5","6","7","8"]

# --- 2. サイドバー (縦並び・大ボタンでクイック追加) ---
with st.sidebar:
    st.header("🏆 試合設定")
    tournament_name = st.text_input("大会名", "練習試合")
    game_date = st.date_input("試合日")
    st.divider()
    
    # === HOME ===
    home_name = st.text_input("自チーム名", "HOME").strip()
    
    # 横分割をやめて、縦並びにしてボタン幅を最大化
    new_h = st.text_input(f"🔵 新規選手を追加", placeholder="例: 99")
    if st.button("＋追加＆出場", key="add_h", use_container_width=True):
        if new_h:
            nums = [x.strip() for x in new_h.split(",") if x.strip()]
            all_h_list = [n.strip() for n in st.session_state.r_str_h.split(",") if n.strip()]
            for n in nums:
                if n not in all_h_list: all_h_list.append(n)
                if n not in st.session_state.act_h: st.session_state.act_h.append(n)
            st.session_state.r_str_h = ",".join(all_h_list)
            st.rerun()

    # 長い名簿は折りたたむ
    with st.expander(f"👥 {home_name} 名簿を手動編集"):
        st.session_state.r_str_h = st.text_area("全背番号 (カンマ区切り)", st.session_state.r_str_h, key="ta_h")
    
    all_h = [n.strip() for n in st.session_state.r_str_h.split(",") if n.strip()]
    valid_act_h = [x for x in st.session_state.act_h if x in all_h]
    st.session_state.act_h = st.multiselect(f"🔵 {home_name} オンコート", all_h, default=valid_act_h)
    active_h = st.session_state.act_h
    
    st.divider()
    
    # === AWAY ===
    away_name = st.text_input("相手チーム名", "AWAY").strip()
    
    new_a = st.text_input(f"🔴 新規選手を追加", placeholder="例: 99", key="in_a")
    if st.button("＋追加＆出場", key="add_a", use_container_width=True):
        if new_a:
            nums = [x.strip() for x in new_a.split(",") if x.strip()]
            all_a_list = [n.strip() for n in st.session_state.r_str_a.split(",") if n.strip()]
            for n in nums:
                if n not in all_a_list: all_a_list.append(n)
                if n not in st.session_state.act_a: st.session_state.act_a.append(n)
            st.session_state.r_str_a = ",".join(all_a_list)
            st.rerun()

    with st.expander(f"👥 {away_name} 名簿を手動編集"):
        st.session_state.r_str_a = st.text_area("全背番号 (カンマ区切り)", st.session_state.r_str_a, key="ta_a")
    
    all_a = [n.strip() for n in st.session_state.r_str_a.split(",") if n.strip()]
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
    st.session_state.current_q = st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True)
    st.divider()

    # HOME：オンコートのみ
    st.write(f"🔵 **{home_name}**")
    if not active_h: st.warning("サイドバーで選手を選んでください")
    else:
        cols_h = st.columns(len(active_h))
        for i, p_num in enumerate(active_h):
            if cols_h[i].button(p_num, key=f"h_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': home_name}; st.session_state.mode = "項目選択"; st.rerun()
    if st.button(f"⏰ {home_name} TOUT", use_container_width=True): record("TOUT", team=home_name, name="TEAM")

    st.divider()
    with st.container(border=True):
        if st.session_state.mode == "選手選択": 
            st.info("選手をタップ")
            
        elif st.session_state.mode == "項目選択":
            st.write(f"**#{st.session_state.tmp.get('player')}**")
            c = st.columns(3)
            if c[0].button("2P", use_container_width=True, type="primary"): st.session_state.tmp['item']="2P"; st.session_state.mode="エリア選択"; st.rerun()
            if c[1].button("3P", use_container_width=True, type="primary"): st.session_state.tmp['item']="3P"; st.session_state.mode="エリア選択"; st.rerun()
            if c[2].button("FT", use_container_width=True): st.session_state.tmp['item']="FT"; st.session_state.mode="結果選択"; st.rerun()
            o = st.columns(3)
            with o[0]:
                if st.button("OR", use_container_width=True): record("OR"); st.rerun()
                if st.button("DR", use_container_width=True): record("DR"); st.rerun()
            with o[1]:
                if st.button("AST", use_container_width=True): record("AST"); st.rerun()
                if st.button("STL", use_container_width=True): record("STL"); st.rerun()
            with o[2]:
                if st.button("F", use_container_width=True): record("Foul"); st.rerun()
            
            st.write("▼ TurnOver")
            to_cols = st.columns(4)
            for i, val in enumerate(["TV", "DD", "PM", "24S"]):
                if to_cols[i].button(val, use_container_width=True): record("TO", val); st.rerun()
            if st.button("キャンセル", use_container_width=True): st.session_state.mode="選手選択"; st.rerun()
            
        elif st.session_state.mode == "エリア選択":
            it = st.session_state.tmp.get('item', '2P')
            st.write(f"🎯 {it} エリア")
            
            if it == "2P":
                r1, r2, r3 = st.columns(3), st.columns(3), st.columns(5)
                areas = ["左下", "中下", "右下", "左レ", "中レ", "右レ", "左角", "左45", "中", "右45", "右角"]
                for i in range(3):
                    if r1[i].button(areas[i], use_container_width=True): st.session_state.tmp['area']=areas[i]; st.session_state.mode="結果選択"; st.rerun()
                for i in range(3):
                    if r2[i].button(areas[i+3], use_container_width=True): st.session_state.tmp['area']=areas[i+3]; st.session_state.mode="結果選択"; st.rerun()
                for i in range(5):
                    if r3[i].button(areas[i+6], use_container_width=True): st.session_state.tmp['area']=areas[i+6]; st.session_state.mode="結果選択"; st.rerun()
            else:
                st.info("外周エリアを選択")
                r_3p_1 = st.columns(3)
                if r_3p_1[0].button("左角", use_container_width=True): st.session_state.tmp['area']="左角"; st.session_state.mode="結果選択"; st.rerun()
                if r_3p_1[1].button("左45", use_container_width=True): st.session_state.tmp['area']="左45"; st.session_state.mode="結果選択"; st.rerun()
                if r_3p_1[2].button("中", use_container_width=True): st.session_state.tmp['area']="中"; st.session_state.mode="結果選択"; st.rerun()
                
                r_3p_2 = st.columns(3)
                if r_3p_2[0].button("右45", use_container_width=True): st.session_state.tmp['area']="右45"; st.session_state.mode="結果選択"; st.rerun()
                if r_3p_2[1].button("右角", use_container_width=True): st.session_state.tmp['area']="右角"; st.session_state.mode="結果選択"; st.rerun()

            if st.button("戻る", use_container_width=True): st.session_state.mode="項目選択"; st.rerun()
            
        elif st.session_state.mode == "結果選択":
            st.write(f"🎯 {st.session_state.tmp.get('area', 'FT')}")
            sc = st.columns(2)
            item = st.session_state.tmp.get('item', '2P')
            pts = {"2P": 2, "3P": 3, "FT": 1}.get(item, 0)
            
            # --- ★自動アシスト連携機能 ---
            if sc[0].button("SUCCESS", use_container_width=True, type="primary"):
                record(item, detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts)
                if item in ["2P", "3P"]:
                    st.session_state.mode = "アシスト選択"
                st.rerun()
                
            if sc[1].button("MISS", use_container_width=True): 
                record(item, detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0)
                st.rerun()
            if st.button("戻る", use_container_width=True): 
                st.session_state.mode="エリア選択" if "P" in item else "項目選択"; st.rerun()

        # --- ★アシスト選択画面 ---
        elif st

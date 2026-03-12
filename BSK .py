import streamlit as st
import pandas as pd
import io
import re
import os
import json
import altair as alt

# ページ設定
st.set_page_config(page_title="バスケ分析Pro V11.2", layout="centered")

# --- 0. CSS注入 ---
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

# --- オートセーブ機能 ---
def save_state():
    if 'history' in st.session_state:
        st.session_state.history.to_csv("auto_save_log.csv", index=False, encoding='utf_8_sig')
    settings = {
        'tournament_name': st.session_state.get('tournament_name', '練習試合'),
        'home_name': st.session_state.get('home_name', 'HOME'),
        'away_name': st.session_state.get('away_name', 'AWAY'),
        'r_str_h': st.session_state.get('r_str_h', '4,5,6,7,8,9,10,11,12,13,14,15'),
        'act_h': st.session_state.get('act_h', ['4','5','6','7','8']),
        'r_str_a': st.session_state.get('r_str_a', '4,5,6,7,8,9,10,11,12,13,14,15'),
        'act_a': st.session_state.get('act_a', ['4','5','6','7','8']),
        'current_q': st.session_state.get('current_q', '1Q')
    }
    with open("auto_save_settings.json", "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False)

def safe_rerun():
    save_state()
    st.rerun()

def safe_sort_key(x):
    m = re.search(r'\d+', str(x))
    if m:
        try: return (0, int(m.group()), str(x))
        except: return (1, 0, str(x))
    return (1, 0, str(x))

# --- ★新規：各種コールバック関数（エラー回避用） ---
def reset_all_data():
    if os.path.exists("auto_save_log.csv"): os.remove("auto_save_log.csv")
    if os.path.exists("auto_save_settings.json"): os.remove("auto_save_settings.json")
    keys_to_clear = ['history', 'tournament_name', 'home_name', 'away_name', 'r_str_h', 'r_str_a', 'act_h', 'act_a', 'current_q', 'mode', 'tmp']
    for k in keys_to_clear:
        if k in st.session_state: del st.session_state[k]

def swap_teams():
    # チーム名・名簿・オンコートを安全に入れ替える
    st.session_state.home_name, st.session_state.away_name = st.session_state.away_name, st.session_state.home_name
    st.session_state.r_str_h, st.session_state.r_str_a = st.session_state.r_str_a, st.session_state.r_str_h
    st.session_state.act_h, st.session_state.act_a = st.session_state.act_a, st.session_state.act_h
    save_state()

def add_h_player():
    new_h = st.session_state.get('new_h_input', '')
    if new_h:
        new_nums = [x.strip() for x in new_h.split(",") if x.strip()]
        all_h_list = [x.strip() for x in st.session_state.r_str_h.split(",") if x.strip()]
        curr_act_h = st.session_state.act_h
        for n in new_nums:
            if n not in all_h_list: all_h_list.append(n)
            if n not in curr_act_h: curr_act_h.append(n)
        st.session_state.r_str_h = ",".join(sorted(all_h_list, key=safe_sort_key))
        st.session_state.act_h = curr_act_h
        st.session_state.new_h_input = ""  # 入力欄をクリア
        save_state()

def add_a_player():
    new_a = st.session_state.get('new_a_input', '')
    if new_a:
        new_nums = [x.strip() for x in new_a.split(",") if x.strip()]
        all_a_list = [x.strip() for x in st.session_state.r_str_a.split(",") if x.strip()]
        curr_act_a = st.session_state.act_a
        for n in new_nums:
            if n not in all_a_list: all_a_list.append(n)
            if n not in curr_act_a: curr_act_a.append(n)
        st.session_state.r_str_a = ",".join(sorted(all_a_list, key=safe_sort_key))
        st.session_state.act_a = curr_act_a
        st.session_state.new_a_input = ""  # 入力欄をクリア
        save_state()

# --- 1. 初期化＆セーフティネット ---
if 'app_init' not in st.session_state:
    st.session_state.app_init = True
    if os.path.exists("auto_save_log.csv"):
        try:
            df = pd.read_csv("auto_save_log.csv")
            df['チーム'] = df['チーム'].astype(str).str.strip()
            df['名前'] = df['名前'].astype(str).str.strip()
            df['点数'] = pd.to_numeric(df['点数'], errors='coerce').fillna(0).astype(int)
            st.session_state.history = df
        except: pass
    if os.path.exists("auto_save_settings.json"):
        try:
            with open("auto_save_settings.json", "r", encoding="utf-8") as f:
                s = json.load(f)
            for k, v in s.items():
                st.session_state[k] = v
        except: pass

if 'history' not in st.session_state: st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'tournament_name' not in st.session_state: st.session_state.tournament_name = "練習試合"
if 'home_name' not in st.session_state: st.session_state.home_name = "HOME"
if 'away_name' not in st.session_state: st.session_state.away_name = "AWAY"
if 'r_str_h' not in st.session_state: st.session_state.r_str_h = "4,5,6,7,8,9,10,11,12,13,14,15"
if 'act_h' not in st.session_state: st.session_state.act_h = ["4","5","6","7","8"]
if 'r_str_a' not in st.session_state: st.session_state.r_str_a = "4,5,6,7,8,9,10,11,12,13,14,15"
if 'act_a' not in st.session_state: st.session_state.act_a = ["4","5","6","7","8"]
if 'current_q' not in st.session_state: st.session_state.current_q = "1Q"
if 'mode' not in st.session_state: st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state: st.session_state.tmp = {}

# --- CSV読み込み ---
def load_csv_data():
    if st.session_state.uploaded_file is not None:
        try:
            file_bytes = st.session_state.uploaded_file.getvalue()
            df = pd.read_csv(io.BytesIO(file_bytes))
            if set(['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数']).issubset(df.columns):
                df['チーム'] = df['チーム'].astype(str).str.strip()
                df['名前'] = df['名前'].astype(str).str.strip()
                df['点数'] = pd.to_numeric(df['点数'], errors='coerce').fillna(0).astype(int)
                
                st.session_state.history = df
                teams = [t for t in df['チーム'].unique() if t and str(t).upper() != 'UNKNOWN']
                csv_h, csv_a = st.session_state.home_name, st.session_state.away_name
                if len(teams) == 1:
                    if teams[0] != csv_a: csv_h = teams[0]
                    else: csv_a = teams[0]
                elif len(teams) >= 2:
                    if st.session_state.home_name in teams:
                        csv_h = st.session_state.home_name
                        csv_a = [t for t in teams if t != csv_h][0]
                    elif st.session_state.away_name in teams:
                        csv_a = st.session_state.away_name
                        csv_h = [t for t in teams if t != csv_a][0]
                    else:
                        csv_h, csv_a = teams[0], teams[1]

                st.session_state.home_name = csv_h
                st.session_state.away_name = csv_a
                
                def extract_exact_players(team_name):
                    p_list = df[df['チーム'] == team_name]['名前'].dropna().unique()
                    res = []
                    for p in p_list:
                        p_str = str(p).strip()
                        if p_str.endswith('番'): p_str = p_str[:-1]
                        if p_str.upper() not in ['TEAM', 'NAN', 'NONE', '']: res.append(p_str)
                    return sorted(res, key=safe_sort_key)
                
                h_p = extract_exact_players(csv_h)
                if h_p:
                    st.session_state.r_str_h = ",".join(h_p)
                    st.session_state.act_h = h_p[:5]
                a_p = extract_exact_players(csv_a)
                if a_p:
                    st.session_state.r_str_a = ",".join(a_p)
                    st.session_state.act_a = a_p[:5]
                        
                st.toast("✅ データを完全に復元しました！")
                save_state()
            else:
                st.error("対応していないCSV形式です。")
        except Exception as e:
            st.error(f"読み込みエラー: {e}")

# --- 2. サイドバー ---
with st.sidebar:
    st.header("🏆 試合設定")
    st.text_input("大会名", key="tournament_name")
    st.divider()
    
    # === HOME ===
    st.text_input("自チーム名", key="home_name")
    st.text_input(f"🔵 新規選手を追加", placeholder="例: 13。", key="new_h_input")
    st.button("＋追加＆出場", key="add_h", use_container_width=True, on_click=add_h_player)

    with st.expander(f"👥 {st.session_state.home_name} 名簿を手動編集"):
        st.text_area("全背番号 (カンマ区切り)", key="r_str_h")
    
    all_h = [x.strip() for x in st.session_state.r_str_h.split(",") if x.strip()]
    valid_act_h = [x for x in st.session_state.act_h if x in all_h]
    if st.session_state.act_h != valid_act_h: st.session_state.act_h = valid_act_h
    st.multiselect(f"🔵 {st.session_state.home_name} オンコート", options=all_h, key="act_h")
    
    # ★修正：入れ替えボタンをコールバック化
    st.divider()
    st.button("🔁 HOMEとAWAYを入れ替える", use_container_width=True, on_click=swap_teams)
    st.divider()
    
    # === AWAY ===
    st.text_input("相手チーム名", key="away_name")
    st.text_input(f"🔴 新規選手を追加", placeholder="例: ⑨", key="new_a_input")
    st.button("＋追加＆出場", key="add_a", use_container_width=True, on_click=add_a_player)

    with st.expander(f"👥 {st.session_state.away_name} 名簿を手動編集"):
        st.text_area("全背番号 (カンマ区切り)", key="r_str_a")
    
    all_a = [x.strip() for x in st.session_state.r_str_a.split(",") if x.strip()]
    valid_act_a = [x for x in st.session_state.act_a if x in all_a]
    if st.session_state.act_a != valid_act_a: st.session_state.act_a = valid_act_a
    st.multiselect(f"🔴 {st.session_state.away_name} オンコート", options=all_a, key="act_a")
    st.divider()
    
    with st.expander("📂 過去データを復元・確認 (CSV読込)"):
        st.write("詳細ログCSVを選択すると、当時のメンバー名簿で上書きされます。")
        st.file_uploader("詳細ログCSVを選択", type=["csv"], label_visibility="collapsed", key="uploaded_file", on_change=load_csv_data)
    
    st.divider()
    st.button("🚨 全データリセット (新規試合)", type="primary", use_container_width=True, on_click=reset_all_data)

# --- 3. 共通記録関数 ---
def record(item, detail="-", res="成功", pts=0, team=None, name=None):
    t_name = team if team else st.session_state.tmp.get('team', 'UNKNOWN')
    p_name = name if name else (f"{st.session_state.tmp['player']}番" if 'player' in st.session_state.tmp else "TEAM")
    new_id = st.session_state.history['id'].max() + 1 if not st.session_state.history.empty else 1
    new_row = pd.DataFrame([{'id': new_id, 'Q': st.session_state.current_q, 'チーム': t_name, '名前': p_name, '項目': item, '詳細': detail, '結果': res, '点数': pts}])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.session_state.mode = "選手選択"; st.toast(f"記録完了")
    save_state()

# --- 4. メイン画面 ---
tab_input, tab_report, tab_edit = st.tabs(["✍️ 記録入力", "📄 統計レポート", "🛠 修正"])

with tab_input:
    if not st.session_state.history.empty:
        try:
            qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[st.session_state.home_name, st.session_state.away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            qs['Total'] = qs.sum(axis=1); st.table(qs.astype(int))
        except: pass
    st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed", key="current_q")

    st.write(f"🔵 **{st.session_state.home_name}**")
    if not st.session_state.act_h: st.warning("サイドバーで選手を選んでください")
    else:
        cols_h = st.columns(len(st.session_state.act_h))
        for i, p_num in enumerate(st.session_state.act_h):
            if cols_h[i].button(p_num, key=f"h_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': st.session_state.home_name}; st.session_state.mode = "項目選択"; safe_rerun()
    if st.button(f"⏰ {st.session_state.home_name} TOUT", use_container_width=True): record("TOUT", team=st.session_state.home_name, name="TEAM"); safe_rerun()

    st.divider()
    with st.container(border=True):
        if st.session_state.mode == "選手選択": st.info("選手をタップ")
        elif st.session_state.mode == "項目選択":
            st.write(f"**#{st.session_state.tmp.get('player')}**")
            c = st.columns(3)
            if c[0].button("2P", use_container_width=True, type="primary"): st.session_state.tmp['item']="2P"; st.session_state.mode="エリア選択"; safe_rerun()
            if c[1].button("3P", use_container_width=True, type="primary"): st.session_state.tmp['item']="3P"; st.session_state.mode="エリア選択"; safe_rerun()
            if c[2].button("FT", use_container_width=True): st.session_state.tmp['item']="FT"; st.session_state.mode="結果選択"; safe_rerun()
            o = st.columns(3)
            with o[0]:
                if st.button("OR", use_container_width=True): record("OR"); safe_rerun()
                if st.button("DR", use_container_width=True): record("DR"); safe_rerun()
            with o[1]:
                if st.button("AST", use_container_width=True): record("AST"); safe_rerun()
                if st.button("STL", use_container_width=True): record("STL"); safe_rerun()
            with o[2]:
                if st.button("F", use_container_width=True): record("Foul"); safe_rerun()
            st.write("▼ TurnOver")
            to_cols = st.columns(4)
            for i, val in enumerate(["TV", "DD", "PM", "24S"]):
                if to_cols[i].button(val, use_container_width=True): record("TO", val); safe_rerun()
            if st.button("キャンセル", use_container_width=True): st.session_state.mode="選手選択"; safe_rerun()
            
        elif st.session_state.mode == "エリア選択":
            it = st.session_state.tmp.get('item', '2P')
            st.write(f"🎯 {it} エリア")
            if it == "2P":
                r1, r2, r3 = st.columns(3), st.columns(3), st.columns(5)
                areas = ["左下", "中下", "右下", "左レ", "中レ", "右レ", "左角", "左45", "中", "右45", "右角"]
                for i in range(3):
                    if r1[i].button(areas[i], use_container_width=True): st.session_state.tmp['area']=areas[i]; st.session_state.mode="結果選択"; safe_rerun()
                for i in range(3):
                    if r2[i].button(areas[i+3], use_container_width=True): st.session_state.tmp['area']=areas[i+3]; st.session_state.mode="結果選択"; safe_rerun()
                for i in range(5):
                    if r3[i].button(areas[i+6], use_container_width=True): st.session_state.tmp['area']=areas[i+6]; st.session_state.mode="結果選択"; safe_rerun()
            else:
                st.info("外周エリアを選択")
                r_3p_1 = st.columns(3)
                if r_3p_1[0].button("左角", use_container_width=True): st.session_state.tmp['area']="左角"; st.session_state.mode="結果選択"; safe_rerun()
                if r_3p_1[1].button("左45", use_container_width=True): st.session_state.tmp['area']="左45"; st.session_state.mode="結果選択"; safe_rerun()
                if r_3p_1[2].button("中", use_container_width=True): st.session_state.tmp['area']="中"; st.session_state.mode="結果選択"; safe_rerun()
                r_3p_2 = st.columns(3)
                if r_3p_2[0].button("右45", use_container_width=True): st.session_state.tmp['area']="右45"; st.session_state.mode="結果選択"; safe_rerun()
                if r_3p_2[1].button("右角", use_container_width=True): st.session_state.tmp['area']="右角"; st.session_state.mode="結果選択"; safe_rerun()
            if st.button("戻る", use_container_width=True): st.session_state.mode="項目選択"; safe_rerun()
            
        elif st.session_state.mode == "結果選択":
            st.write(f"🎯 {st.session_state.tmp.get('area', 'FT')}")
            sc = st.columns(2)
            item = st.session_state.tmp.get('item', '2P')
            pts = {"2P": 2, "3P": 3, "FT": 1}.get(item, 0)
            
            if sc[0].button("SUCCESS", use_container_width=True, type="primary"):
                record(item, detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts)
                if item in ["2P", "3P"]: st.session_state.mode = "アシスト選択"
                safe_rerun()
            if sc[1].button("MISS", use_container_width=True): 
                record(item, detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0)
                safe_rerun()
            if st.button("戻る", use_container_width=True): 
                st.session_state.mode="エリア選択" if "P" in item else "項目選択"; safe_rerun()

        elif st.session_state.mode == "アシスト選択":
            scorer = st.session_state.tmp.get('player')
            t_name = st.session_state.tmp.get('team')
            st.write(f"🏀 **#{scorer}** 得点！アシストは？")
            
            active_list = st.session_state.act_h if t_name == st.session_state.home_name else st.session_state.act_a
            assist_candidates = [p for p in active_list if p != scorer]
            
            if assist_candidates:
                ast_c = st.columns(len(assist_candidates))
                for i, p_num in enumerate(assist_candidates):
                    if ast_c[i].button(p_num, key=f"ast_{p_num}", use_container_width=True):
                        record("AST", detail=f"to #{scorer}", res="成功", pts=0, team=t_name, name=f"{p_num}番")
                        safe_rerun()
            st.divider()
            if st.button("❌ アシストなし", use_container_width=True):
                st.session_state.mode = "選手選択"
                safe_rerun()

    st.divider()
    if st.button(f"⏰ {st.session_state.away_name} TOUT", use_container_width=True): record("TOUT", team=st.session_state.away_name, name="TEAM"); safe_rerun()
    st.write(f"🔴 **{st.session_state.away_name}**")
    if not st.session_state.act_a: st.warning("サイドバーで選手を選んでください")
    else:
        cols_a = st.columns(len(st.session_state.act_a))
        for i, p_num in enumerate(st.session_state.act_a):
            if cols_a[i].button(p_num, key=f"a_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': st.session_state.away_name}; st.session_state.mode = "項目選択"; safe_rerun()

# --- グラフ描画用関数 ---
def draw_stacked_chart(df, x_col, max_y):
    if df.empty: return
    df_m = df.reset_index().melt(id_vars=x_col, var_name='結果', value_name='回数')
    chart = alt.Chart(df_m).mark_bar().encode(
        x=alt.X(f"{x_col}:N", sort=None, title='', axis=alt.Axis(labelAngle=-45, labelOverlap=False)),
        y=alt.Y('回数:Q', scale=alt.Scale(domain=[0, max_y]), title=''),
        color=alt.Color('結果:N', scale=alt.Scale(domain=['成功', '失敗'], range=['#00b050', '#ff4b4b']), legend=alt.Legend(title="", orient="bottom")),
        tooltip=[f"{x_col}:N", '結果:N', '回数:Q']
    ).properties(height=250)
    st.altair_chart(chart, use_container_width=True)

def draw_simple_bar_chart(s, x_name, max_y, sort_order, color_range=None):
    if s.empty: return
    df = s.to_frame(name='回数').reset_index()
    df.columns = [x_name, '回数']
    color_encode = alt.Color(f'{x_name}:N', legend=None)
    if color_range:
        color_encode = alt.Color(f'{x_name}:N', scale=alt.Scale(domain=sort_order, range=color_range), legend=None)
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f"{x_name}:N", sort=sort_order, title='', axis=alt.Axis(labelAngle=0, labelOverlap=False)),
        y=alt.Y('回数:Q', scale=alt.Scale(domain=[0, max_y]), title=''),
        color=color_encode,
        tooltip=[f"{x_name}:N", '回数:Q']
    ).properties(height=200)
    st.altair_chart(chart, use_container_width=True)

# --- 【タブ2】レポート ---
with tab_report:
    if st.session_state.history.empty: st.info("データなし")
    else:
        st.header("1. スコア推移")
        try:
            rep_qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[st.session_state.home_name, st.session_state.away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            rep_qs['Total'] = rep_qs.sum(axis=1); st.table(rep_qs.astype(int))
        except: pass

        st.header("2. 分析グラフ")
        st.write("▼ グラフ表示の対象期間")
        selected_q_graph = st.radio("グラフ対象期間", ["Total", "1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")
        
        if selected_q_graph == "Total": filtered_history = st.session_state.history
        else: filtered_history = st.session_state.history[st.session_state.history['Q'] == selected_q_graph]

        st.subheader(f"① 全体シュート ({selected_q_graph})")
        shots_df = filtered_history[filtered_history['項目'].isin(['2P', '3P', 'FT'])]
        if not shots_df.empty:
            st.markdown("<span style='font-size:11px;'>全体の高さ＝「試行回数」、緑色が「成功」、赤色が「失敗」</span>", unsafe_allow_html=True)
            s_stats = shots_df.groupby(['チーム', '項目', '結果']).size().unstack(fill_value=0)
            if '成功' not in s_stats.columns: s_stats['成功'] = 0
            if '失敗' not in s_stats.columns: s_stats['失敗'] = 0
            s_stats = s_stats[['成功', '失敗']]
            max_y_overall = int(s_stats.sum(axis=1).max()); max_y_overall = max_y_overall + 1 if max_y_overall > 0 else 5
            
            g1, g2 = st.columns(2)
            with g1:
                st.write(f"🔵 **{st.session_state.home_name}**")
                if st.session_state.home_name in s_stats.index.get_level_values('チーム'):
                    draw_stacked_chart(s_stats.xs(st.session_state.home_name, level='チーム').reindex(['2P', '3P', 'FT'], fill_value=0), '項目', max_y_overall)
                else: st.caption("データなし")
            with g2:
                st.write(f"🔴 **{st.session_state.away_name}**")
                if st.session_state.away_name in s_stats.index.get_level_values('チーム'):
                    draw_stacked_chart(s_stats.xs(st.session_state.away_name, level='チーム').reindex(['2P', '3P', 'FT'], fill_value=0), '項目', max_y_overall)
                else: st.caption("データなし")
        else: st.info(f"{selected_q_graph} のシュート記録がありません")

        st.subheader(f"② エリア別シュート分布 ({selected_q_graph})")
        area_target = st.radio("表示項目", ["2P", "3P"], horizontal=True, label_visibility="collapsed")
        area_df = filtered_history[filtered_history['項目'] == area_target]
        if not area_df.empty:
            a_stats = area_df.groupby(['チーム', '詳細', '結果']).size().unstack(fill_value=0)
            if '成功' not in a_stats.columns: a_stats['成功'] = 0
            if '失敗' not in a_stats.columns: a_stats['失敗'] = 0
            a_stats = a_stats[['成功', '失敗']]
            max_y_area = int(a_stats.sum(axis=1).max()); max_y_area = max_y_area + 1 if max_y_area > 0 else 5
            areas_order = ["左下", "中下", "右下", "左レ", "中レ", "右レ", "左角", "左45", "中", "右45", "右角"] if area_target == "2P" else ["左角", "左45", "中", "右45", "右角"]
            
            ga1, ga2 = st.columns(2)
            with ga1:
                st.write(f"🔵 **{st.session_state.home_name}**")
                if st.session_state.home_name in a_stats.index.get_level_values('チーム'):
                    draw_stacked_chart(a_stats.xs(st.session_state.home_name, level='チーム').reindex(areas_order, fill_value=0), '詳細', max_y_area)
                else: st.caption("データなし")
            with ga2:
                st.write(f"🔴 **{st.session_state.away_name}**")
                if st.session_state.away_name in a_stats.index.get_level_values('チーム'):
                    draw_stacked_chart(a_stats.xs(st.session_state.away_name, level='チーム').reindex(areas_order, fill_value=0), '詳細', max_y_area)
                else: st.caption("データなし")
        else: st.info(f"{selected_q_graph} の {area_target}シュート記録がありません")

        st.subheader(f"③ リバウンド ({selected_q_graph})")
        reb_df = filtered_history[filtered_history['項目'].isin(['OR', 'DR'])]
        if not reb_df.empty:
            r_stats = reb_df.groupby(['チーム', '項目']).size().unstack(fill_value=0)
            if 'OR' not in r_stats.columns: r_stats['OR'] = 0
            if 'DR' not in r_stats.columns: r_stats['DR'] = 0
            r_stats = r_stats[['OR', 'DR']]
            max_y_reb = int(r_stats.max().max()); max_y_reb = max_y_reb + 1 if max_y_reb > 0 else 5
            
            gr1, gr2 = st.columns(2)
            with gr1:
                st.write(f"🔵 **{st.session_state.home_name}**")
                if st.session_state.home_name in r_stats.index:
                    draw_simple_bar_chart(r_stats.loc[st.session_state.home_name], '種類', max_y_reb, ['OR', 'DR'], ['#ff9f43', '#3498db'])
                else: st.caption("データなし")
            with gr2:
                st.write(f"🔴 **{st.session_state.away_name}**")
                if st.session_state.away_name in r_stats.index:
                    draw_simple_bar_chart(r_stats.loc[st.session_state.away_name], '種類', max_y_reb, ['OR', 'DR'], ['#ff9f43', '#3498db'])
                else: st.caption("データなし")
        else: st.info(f"{selected_q_graph} のリバウンド記録がありません")

        st.subheader(f"④ ターンオーバー ({selected_q_graph})")
        to_df = filtered_history[filtered_history['項目'] == 'TO']
        if not to_df.empty:
            to_stats = to_df.groupby(['チーム', '詳細']).size().unstack(fill_value=0)
            to_cols = ['TV', 'DD', 'PM', '24S']
            for col in to_cols:
                if col not in to_stats.columns: to_stats[col] = 0
            to_stats = to_stats[to_cols]
            max_y_to = int(to_stats.max().max()); max_y_to = max_y_to + 1 if max_y_to > 0 else 5
            
            gt1, gt2 = st.columns(2)
            with gt1:
                st.write(f"🔵 **{st.session_state.home_name}**")
                if st.session_state.home_name in to_stats.index:
                    draw_simple_bar_chart(to_stats.loc[st.session_state.home_name], '詳細', max_y_to, to_cols, ['#95a5a6', '#95a5a6', '#95a5a6', '#95a5a6'])
                else: st.caption("データなし")
            with gt2:
                st.write(f"🔴 **{st.session_state.away_name}**")
                if st.session_state.away_name in to_stats.index:
                    draw_simple_bar_chart(to_stats.loc[st.session_state.away_name], '詳細', max_y_to, to_cols, ['#95a5a6', '#95a5a6', '#95a5a6', '#95a5a6'])
                else: st.caption("データなし")
        else: st.info(f"{selected_q_graph} のターンオーバー記録がありません")

        st.header("3. 個人スタッツ")
        def get_stats_df(t_name, p_list_all):
            df = st.session_state.history[st.session_state.history['チーム'] == t_name]
            rows = []
            tp, tm2i, tm2a, tm3i, tm3a, tfi, tfa, tor, tdr, tast, tstl, tf, ttv, tdd, tpm, ts24 = [0]*16
            def fmt_stat(m, a): return f"{m}/{a}\n{(m/a*100):.0f}%" if a > 0 else "0/0\n0%"
            for p_num in p_list_all:
                pn = f"{p_num}番"; pdf = df[df['名前'] == pn]
                m2i, m2a = len(pdf[(pdf['項目']=='2P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='2P'])
                m3i, m3a = len(pdf[(pdf['項目']=='3P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='3P'])
                fi, fa = len(pdf[(pdf['項目']=='FT') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='FT'])
                orb, drb = len(pdf[pdf['項目']=='OR']), len(pdf[pdf['項目']=='DR'])
                ast, stl, f = len(pdf[pdf['項目']=='AST']), len(pdf[pdf['項目']=='STL']), len(pdf[pdf['項目']=='Foul'])
                to = pdf[pdf['項目']=='TO']; tv, dd, pm, s24 = len(to[to['詳細']=='TV']), len(to[to['詳細']=='DD']), len(to[to['詳細']=='PM']), len(to[to['詳細']=='24S'])
                p = pdf['点数'].sum()
                tp+=p; tm2i+=m2i; tm2a+=m2a; tm3i+=m3i; tm3a+=m3a; tfi+=fi; tfa+=fa; tor+=orb; tdr+=drb; tast+=ast; tstl+=stl; tf+=f; ttv+=tv; tdd+=dd; tpm+=pm; ts24+=s24
                rows.append({'#': p_num, 'Pts': p, 'FG\n(M/A)': fmt_stat(m2i+m3i, m2a+m3a), '3P\n(M/A)': fmt_stat(m3i, m3a), 'FT\n(M/A)': fmt_stat(fi, fa), 
                             'REB\n(D/O)': f"{drb+orb}\n({drb}/{orb})", 'As': ast, 'St': stl, 'F': f, 'TO\n(T/D/P/2)': f"{tv+dd+pm+s24}\n({tv}/{dd}/{pm}/{s24})", 'Team': t_name})
            rows.append({'#': 'Total', 'Pts': tp, 'FG\n(M/A)': fmt_stat(tm2i+tm3i, tm2a+tm3a), '3P\n(M/A)': fmt_stat(tm3i, tm3a), 'FT\n(M/A)': fmt_stat(tfi, tfa), 
                         'REB\n(D/O)': f"{tdr+tor}\n({tdr}/{tor})", 'As': tast, 'St': tstl, 'F': tf, 'TO\n(T/D/P/2)': f"{ttv+tdd+tpm+ts24}\n({ttv}/{tdd}/{tpm}/{ts24})", 'Team': t_name})
            return pd.DataFrame(rows)
        
        h_df = get_stats_df(st.session_state.home_name, all_h); a_df = get_stats_df(st.session_state.away_name, all_a)
        st.write(f"🔵 **{st.session_state.home_name}**"); st.table(h_df.drop(columns='Team').set_index('#'))
        st.write(f"🔴 **{st.session_state.away_name}**"); st.table(a_df.drop(columns='Team').set_index('#'))

        st.divider()
        st.header("4. 詳細ログ")
        st.dataframe(st.session_state.history.iloc[::-1], use_container_width=True)
        
        csv_stats = pd.concat([h_df, a_df], ignore_index=True).to_csv(index=False).encode('utf_8_sig')
        st.download_button("📊 統計CSV保存", csv_stats, f"{st.session_state.tournament_name}_stats.csv", "text/csv")
        csv_log = st.session_state.history.to_csv(index=False).encode('utf_8_sig')
        st.download_button("📜 ログCSV保存", csv_log, f"{st.session_state.tournament_name}_log.csv", "text/csv")

with tab_edit:
    st.header("🛠 修正")
    if not st.session_state.history.empty:
        for i, row in st.session_state.history.iloc[::-1].iterrows():
            cols = st.columns([4, 1])
            cols[0].write(f"{row['Q']}|{row['名前']}|{row['項目']}({row['詳細']})")
            if cols[1].button("🗑️", key=f"del_{i}"):
                st.session_state.history = st.session_state.history.drop(i); safe_rerun()

save_state()

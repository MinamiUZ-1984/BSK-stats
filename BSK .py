import streamlit as st
import pandas as pd
import io
import re
import os
import json
import altair as alt
import uuid
import streamlit.components.v1 as components

# ページ設定
st.set_page_config(page_title="バスケ分析Pro V30.0", layout="centered")

# --- 0. CSS注入（PCでの巨大化防止 ＆ 高さ最適化） ---
st.markdown("""
    <style>
    /* ★大改修1：アプリの最大横幅を450pxに固定！PCで見ても巨大化しません★ */
    .block-container { max-width: 450px !important; padding-left: 4px !important; padding-right: 4px !important; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    
    /* カラム間の隙間を極限まで詰める */
    [data-testid="column"] { padding: 0 1px !important; }
    [data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; width: 100% !important; gap: 0px !important; } 
    [data-testid="stHorizontalBlock"] > div { flex: 1 1 0% !important; min-width: 0 !important; }
    
    /* ボタンの高さと文字サイズをスマートに調整 */
    .stButton > button { 
        width: 100% !important; 
        padding: 0px !important; 
        font-size: 15px !important; 
        font-weight: bold !important; 
        min-height: 42px !important; 
        margin-bottom: 0px !important; 
        position: relative; 
        z-index: 1; 
    }
    [data-testid="stVerticalBlock"] { gap: 0.1rem !important; }
    
    div[data-testid="stTable"] table { font-size: 9px !important; width: 100% !important; }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td { padding: 2px 1px !important; line-height: 1.1 !important; }
    
    .court-zone { display: inline-block; font-size: 12px; font-weight: bold; color: white; background-color: #d35400; padding: 3px 12px; border-radius: 15px; margin-top: 5px; margin-bottom: 8px; }
    
    /* ラベルの食い込み位置を調整 */
    .label-wrapper { text-align: center; margin-bottom: -12px; position: relative; z-index: 10; pointer-events: none; }
    .area-label { background: rgba(255, 255, 255, 0.9); border: 1px solid #aaa; border-radius: 3px; font-size: 10px; font-weight: bold; color: #111; padding: 1px 4px; display: inline-block; white-space: nowrap; }
    
    .center-panel-title { text-align:center; font-size:14px; font-weight:bold; color:#fff; background:#2c3e50; padding:6px; border-radius:5px 5px 0 0; margin-bottom: 0px; }
    
    .advice-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #3498db; margin-bottom: 10px; }
    .advice-good { color: #27ae60; font-weight: bold; }
    .advice-bad { color: #c0392b; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- ターゲットを狙い撃ちする精密スクロール ---
def auto_scroll_to_target():
    components.html(
        """
        <script>
            setTimeout(function() {
                const target = window.parent.document.getElementById('scroll-target');
                if (target) {
                    target.scrollIntoView({behavior: 'smooth', block: 'start'});
                    setTimeout(function() {
                        const parent = window.parent;
                        const containers = parent.document.querySelectorAll('.main, [data-testid="stAppViewContainer"], [data-testid="stMain"]');
                        containers.forEach(container => { container.scrollBy({ top: -20, behavior: 'smooth' }); });
                        parent.scrollBy({ top: -20, behavior: 'smooth' });
                    }, 200);
                }
            }, 400); 
        </script>
        """,
        height=0
    )

# --- ユーザーIDの発行 ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'read_only' not in st.session_state:
    st.session_state.read_only = False

# --- 使用者名ログイン＆ロック画面 ---
if 'room_key' not in st.session_state:
    st.title("🏀 バスケ分析Pro")
    st.info("💡 **使用者名** を入力してスタートしてください。")
    room_input = st.text_input("使用者名（例：山田花子 など）")
    col1, col2 = st.columns(2)
    if col1.button("🚪 記録者として入る", type="primary", use_container_width=True):
        if room_input.strip() == "": st.error("使用者名を入力してください！")
        else:
            room = room_input.strip()
            lock_file = f"lock_{room}.txt"
            if os.path.exists(lock_file):
                with open(lock_file, "r") as f: locked_by = f.read()
                if locked_by != st.session_state.user_id:
                    st.session_state.show_lock_warning = room
                    st.rerun()
            with open(lock_file, "w") as f: f.write(st.session_state.user_id)
            st.session_state.room_key = room
            st.session_state.read_only = False
            st.rerun()
    if col2.button("👀 見るだけモード", use_container_width=True):
         if room_input.strip() == "": st.error("使用者名を入力してください！")
         else:
            st.session_state.room_key = room_input.strip()
            st.session_state.read_only = True
            st.rerun()
    if st.session_state.get('show_lock_warning'):
        warn_room = st.session_state.show_lock_warning
        st.warning(f"⚠️ 使用者名「{warn_room}」は現在他の人が記録中です！\n\n・「👀 見るだけモード」で入るか、別の使用者名にしてください。")
        if st.button("🚨 強制的に記録者として奪う（前の人がアプリを閉じた場合）"):
            with open(f"lock_{warn_room}.txt", "w") as f: f.write(st.session_state.user_id)
            st.session_state.room_key = warn_room
            st.session_state.read_only = False
            del st.session_state['show_lock_warning']
            st.rerun()
    st.stop() 

# --- 使用者名に基づいた専用のファイル名 ---
ROOM = st.session_state.room_key
LOG_FILE = f"auto_save_log_{ROOM}.csv"
SET_FILE = f"auto_save_settings_{ROOM}.json"

def save_state():
    if st.session_state.read_only: return 
    if 'history' in st.session_state:
        st.session_state.history.to_csv(LOG_FILE, index=False, encoding='utf_8_sig')
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
    with open(SET_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False)

def safe_rerun():
    st.session_state.report_trigger = False
    st.rerun()

def safe_sort_key(x):
    m = re.search(r'\d+', str(x))
    if m:
        try: return (0, int(m.group()), str(x))
        except: return (1, 0, str(x))
    return (1, 0, str(x))

def reset_all_data():
    if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
    if os.path.exists(SET_FILE): os.remove(SET_FILE)
    keys_to_clear = ['history', 'tournament_name', 'home_name', 'away_name', 'r_str_h', 'r_str_a', 'act_h', 'act_a', 'current_q', 'mode', 'tmp', 'report_trigger']
    for k in keys_to_clear:
        if k in st.session_state: del st.session_state[k]

def swap_teams():
    st.session_state.home_name, st.session_state.away_name = st.session_state.away_name, st.session_state.home_name
    st.session_state.r_str_h, st.session_state.r_str_a = st.session_state.r_str_a, st.session_state.r_str_h
    st.session_state.act_h, st.session_state.act_a = st.session_state.act_a, st.session_state.act_h

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
        st.session_state.new_h_input = ""

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
        st.session_state.new_a_input = ""

def logout_room():
    if not st.session_state.read_only:
        lock_file = f"lock_{st.session_state.room_key}.txt"
        if os.path.exists(lock_file):
            with open(lock_file, "r") as f: locked_by = f.read()
            if locked_by == st.session_state.user_id: os.remove(lock_file)
    del st.session_state['room_key']
    st.session_state.read_only = False

if 'app_init' not in st.session_state:
    st.session_state.app_init = True
    if os.path.exists(LOG_FILE):
        try:
            df = pd.read_csv(LOG_FILE)
            df['チーム'] = df['チーム'].astype(str).str.strip()
            df['名前'] = df['名前'].astype(str).str.strip()
            df['点数'] = pd.to_numeric(df['点数'], errors='coerce').fillna(0).astype(int)
            st.session_state.history = df
        except: pass
    if os.path.exists(SET_FILE):
        try:
            with open(SET_FILE, "r", encoding="utf-8") as f: s = json.load(f)
            for k, v in s.items(): st.session_state[k] = v
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
if 'report_trigger' not in st.session_state: st.session_state.report_trigger = False

def load_csv_data():
    if st.session_state.uploaded_file is not None:
        try:
            file_bytes = st.session_state.uploaded_file.getvalue()
            try: df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf_8_sig')
            except: df = pd.read_csv(io.BytesIO(file_bytes))
            df.columns = [str(c).replace('\ufeff', '').strip() for c in df.columns]

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
                        csv_h = st.session_state.home_name; csv_a = [t for t in teams if t != csv_h][0]
                    elif st.session_state.away_name in teams:
                        csv_a = st.session_state.away_name; csv_h = [t for t in teams if t != csv_a][0]
                    else:
                        csv_h, csv_a = teams[0], teams[1]
                st.session_state.home_name = csv_h; st.session_state.away_name = csv_a
                def extract_exact_players(team_name):
                    p_list = df[df['チーム'] == team_name]['名前'].dropna().unique()
                    res = []
                    for p in p_list:
                        p_str = str(p).strip()
                        if p_str.endswith('番'): p_str = p_str[:-1]
                        if p_str.upper() not in ['TEAM', 'NAN', 'NONE', '']: res.append(p_str)
                    return sorted(res, key=safe_sort_key)
                h_p = extract_exact_players(csv_h)
                if h_p: st.session_state.r_str_h = ",".join(h_p); st.session_state.act_h = h_p[:5]
                a_p = extract_exact_players(csv_a)
                if a_p: st.session_state.r_str_a = ",".join(a_p); st.session_state.act_a = a_p[:5]
                st.session_state.report_trigger = True
                save_state()
                st.toast(f"✅ データを完全に復元しました！")
            else: st.error("対応していないCSV形式です。")
        except Exception as e: st.error(f"読み込みエラー: {e}")

with st.sidebar:
    st.success(f"👤 現在の使用者: **{ROOM}**")
    mode_str = "👀 見るだけモード" if st.session_state.read_only else "✍️ 記録中（編集可）"
    st.caption(f"現在の権限: {mode_str}")
    st.button("⬅️ 退出する（使用者変更）", use_container_width=True, on_click=logout_room)
    st.divider()

    if not st.session_state.read_only:
        st.header("🏆 試合設定")
        st.text_input("大会名", key="tournament_name")
        st.divider()
        st.text_input("自チーム名", key="home_name")
        st.text_input(f"🔵 新規選手を追加", placeholder="例: 13。", key="new_h_input")
        st.button("＋追加＆出場", key="add_h", use_container_width=True, on_click=add_h_player)
        with st.expander(f"👥 {st.session_state.home_name} 名簿を手動編集"): st.text_area("全背番号 (カンマ区切り)", key="r_str_h")
        all_h = [x.strip() for x in st.session_state.r_str_h.split(",") if x.strip()]
        valid_act_h = [x for x in st.session_state.act_h if x in all_h]
        if st.session_state.act_h != valid_act_h: st.session_state.act_h = valid_act_h
        st.multiselect(f"🔵 {st.session_state.home_name} オンコート", options=all_h, key="act_h")
        st.divider()
        st.button("🔁 HOMEとAWAYを入れ替える", use_container_width=True, on_click=swap_teams)
        st.divider()
        st.text_input("相手チーム名", key="away_name")
        st.text_input(f"🔴 新規選手を追加", placeholder="例: ⑨", key="new_a_input")
        st.button("＋追加＆出場", key="add_a", use_container_width=True, on_click=add_a_player)
        with st.expander(f"👥 {st.session_state.away_name} 名簿を手動編集"): st.text_area("全背番号 (カンマ区切り)", key="r_str_a")
        all_a = [x.strip() for x in st.session_state.r_str_a.split(",") if x.strip()]
        valid_act_a = [x for x in st.session_state.act_a if x in all_a]
        if st.session_state.act_a != valid_act_a: st.session_state.act_a = valid_act_a
        st.multiselect(f"🔴 {st.session_state.away_name} オンコート", options=all_a, key="act_a")
        st.divider()
        with st.expander("📂 過去データを復元・確認 (CSV読込)"): st.file_uploader("詳細ログCSVを選択", type=["csv"], label_visibility="collapsed", key="uploaded_file", on_change=load_csv_data)
        st.divider()
        st.button("🚨 全データリセット (新規試合)", type="primary", use_container_width=True, on_click=reset_all_data)
    else:
        st.info("※見るだけモードのため、選手追加やデータリセット等の設定は行えません。")

# --- 共通記録関数 ---
def record(item, detail="-", res="成功", pts=0, team=None, name=None):
    t_name = team if team else st.session_state.tmp.get('team', 'UNKNOWN')
    p_name = name if name else (f"{st.session_state.tmp['player']}番" if 'player' in st.session_state.tmp else "TEAM")
    new_id = st.session_state.history['id'].max() + 1 if not st.session_state.history.empty else 1
    new_row = pd.DataFrame([{'id': new_id, 'Q': st.session_state.current_q, 'チーム': t_name, '名前': p_name, '項目': item, '詳細': detail, '結果': res, '点数': pts}])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.session_state.mode = "選手選択"; st.toast(f"記録完了")

# --- ★大改修：⭕❌ボタンの幅を「30px」に強制固定するためのグリッド！★ ---
def draw_zone(col, area_name, key_prefix, item_type):
    with col:
        st.markdown(f"<div class='label-wrapper'><div class='area-label'>{area_name}</div></div>", unsafe_allow_html=True)
        pts = 2 if item_type == "2P" else 3
        
        # 見えない5つのマスを作り、「⭕」と「❌」の幅を約27%(30px)に固定！
        z_cols = st.columns([2.2, 3.0, 0.6, 3.0, 2.2])
        
        if z_cols[1].button("⭕", key=f"{key_prefix}_o", type="primary", use_container_width=True):
            record(item_type, detail=area_name, res="成功", pts=pts)
            st.session_state.mode = "アシスト選択"
            safe_rerun()
        if z_cols[3].button("❌", key=f"{key_prefix}_x", use_container_width=True):
            record(item_type, detail=area_name, res="失敗", pts=0)
            st.session_state.mode = "リバウンド選択"
            safe_rerun()

# --- センターパネル用：アクションメニュー描画関数 ---
def draw_action_menu():
    player_num = st.session_state.tmp.get('player')
    team_name = st.session_state.tmp.get('team')
    t_icon = "🔵" if team_name == st.session_state.home_name else "🔴"
    
    st.markdown(f"<div id='scroll-target'></div><div class='center-panel-title'>{t_icon} {team_name} : #{player_num} 操作パネル</div>", unsafe_allow_html=True)
    with st.container(border=True):
        if st.session_state.mode == "項目選択":
            c = st.columns(3)
            if c[0].button("2P", use_container_width=True, type="primary"): st.session_state.tmp['item']="2P"; st.session_state.mode="エリア＆結果選択"; safe_rerun()
            if c[1].button("3P", use_container_width=True, type="primary"): st.session_state.tmp['item']="3P"; st.session_state.mode="エリア＆結果選択"; safe_rerun()
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
            
            st.divider()
            if st.button("❌ キャンセル", use_container_width=True): st.session_state.mode="選手選択"; safe_rerun()
            auto_scroll_to_target()
            
        elif st.session_state.mode == "エリア＆結果選択":
            it = st.session_state.tmp.get('item', '2P')
            if it == "2P":
                st.markdown("<div style='text-align:center;'><span class='court-zone'>【 2P エリア 】</span></div>", unsafe_allow_html=True)
                
                # 🏀 第1行目：左角(24) | 空(1) | 左下(24) | 🗑️(2) | 右下(24) | 空(1) | 右角(24)
                r1 = st.columns([24, 1, 24, 2, 24, 1, 24])
                draw_zone(r1[0], "左角", "2p_lcor", "2P")
                draw_zone(r1[2], "左下", "2p_lbl", "2P")
                with r1[3]:
                    st.markdown("<div style='text-align:center; font-size:18px; margin-top:20px;'>🗑️</div>", unsafe_allow_html=True)
                draw_zone(r1[4], "右下", "2p_rbl", "2P")
                draw_zone(r1[6], "右角", "2p_rcor", "2P")

                # 🏀 第2行目：左レ(24) | 中下(24) | 右レ(24)
                r2 = st.columns([9, 24, 5, 24, 5, 24, 9])
                draw_zone(r2[1], "左レ", "2p_ll", "2P")
                draw_zone(r2[3], "中下", "2p_cbl", "2P")
                draw_zone(r2[5], "右レ", "2p_rl", "2P")

                # 🏀 第3行目：左45(24) | 中レ(24) | 右45(24)
                r3 = st.columns([13, 24, 1, 24, 1, 24, 13])
                draw_zone(r3[1], "左45", "2p_l45", "2P")
                draw_zone(r3[3], "中レ", "2p_cl", "2P")
                draw_zone(r3[5], "右45", "2p_r45", "2P")

                # 🏀 第4行目：中(24)
                r4 = st.columns([38, 24, 38])
                draw_zone(r4[1], "中", "2p_c", "2P")

            else: 
                # 3P
                st.markdown("<div style='text-align:center; font-size:35px; margin-top:-10px; margin-bottom:5px;'>🗑️🏀</div>", unsafe_allow_html=True)
                st.markdown("<div style='text-align:center; font-size:16px; color:#ccc; margin-bottom:10px;'>🔺 ペイントエリア 🔺</div>", unsafe_allow_html=True)
                st.markdown("<div style='text-align:center;'><span class='court-zone'>【 3P エリア 】</span></div>", unsafe_allow_html=True)
                
                r3p_1 = st.columns([24, 52, 24])
                draw_zone(r3p_1[0], "左角", "3p_lcor", "3P")
                draw_zone(r3p_1[2], "右角", "3p_rcor", "3P")
                
                r3p_2 = st.columns([12, 24, 28, 24, 12])
                draw_zone(r3p_2[1], "左45", "3p_l45", "3P")
                draw_zone(r3p_2[3], "右45", "3p_r45", "3P")
                
                r3p_3 = st.columns([38, 24, 38])
                draw_zone(r3p_3[1], "中", "3p_c", "3P")

            st.divider()
            if st.button("🔙 戻る", use_container_width=True): st.session_state.mode="項目選択"; safe_rerun()
            auto_scroll_to_target()

        elif st.session_state.mode == "結果選択": # FT用
            st.write(f"🎯 {st.session_state.tmp.get('area', 'FT')}")
            sc = st.columns(2)
            item = st.session_state.tmp.get('item', 'FT')
            if sc[0].button("SUCCESS", use_container_width=True, type="primary"):
                record(item, detail=st.session_state.tmp.get('area','-'), res="成功", pts=1)
                safe_rerun()
            if sc[1].button("MISS", use_container_width=True): 
                record(item, detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0)
                st.session_state.mode = "リバウンド選択"
                safe_rerun()
            st.divider()
            if st.button("🔙 戻る", use_container_width=True): st.session_state.mode="項目選択"; safe_rerun()
            auto_scroll_to_target()

        elif st.session_state.mode == "アシスト選択":
            st.write(f"🏀 得点！アシストは？")
            active_list = st.session_state.act_h if team_name == st.session_state.home_name else st.session_state.act_a
            assist_candidates = [p for p in active_list if p != player_num]
            if assist_candidates:
                ast_c = st.columns(len(assist_candidates))
                for i, p_num in enumerate(assist_candidates):
                    if ast_c[i].button(p_num, key=f"ast_{p_num}", use_container_width=True):
                        record("AST", detail=f"to #{player_num}", res="成功", pts=0, team=team_name, name=f"{p_num}番")
                        safe_rerun()
            st.divider()
            if st.button("❌ アシストなし", use_container_width=True): st.session_state.mode = "選手選択"; safe_rerun()
            auto_scroll_to_target()

        elif st.session_state.mode == "リバウンド選択":
            shooter_team = st.session_state.tmp.get('team')
            st.error(f"🗑️ シュートミス！ 誰がリバウンドを取った？")
            
            st.caption(f"🔵 {st.session_state.home_name}")
            reb_h_cols = st.columns(len(st.session_state.act_h))
            for i, p_num in enumerate(st.session_state.act_h):
                if reb_h_cols[i].button(p_num, key=f"reb_h_{p_num}", use_container_width=True):
                    reb_type = "OR" if st.session_state.home_name == shooter_team else "DR"
                    record(reb_type, team=st.session_state.home_name, name=f"{p_num}番")
                    safe_rerun()

            st.caption(f"🔴 {st.session_state.away_name}")
            reb_a_cols = st.columns(len(st.session_state.act_a))
            for i, p_num in enumerate(st.session_state.act_a):
                if reb_a_cols[i].button(p_num, key=f"reb_a_{p_num}", use_container_width=True):
                    reb_type = "OR" if st.session_state.away_name == shooter_team else "DR"
                    record(reb_type, team=st.session_state.away_name, name=f"{p_num}番")
                    safe_rerun()
            
            st.divider()
            if st.button("⏩ リバウンド記録なし（スキップ）", use_container_width=True): st.session_state.mode = "選手選択"; safe_rerun()
            auto_scroll_to_target()

def draw_stacked_chart(df, x_col, max_y):
    if df.empty: return
    df_m = df.reset_index().melt(id_vars=x_col, var_name='結果', value_name='回数')
    bars = alt.Chart(df_m).mark_bar().encode(
        x=alt.X(f"{x_col}:N", sort=None, title='', axis=alt.Axis(labelAngle=-45, labelOverlap=False)),
        y=alt.Y('回数:Q', scale=alt.Scale(domain=[0, max_y]), title=''),
        color=alt.Color('結果:N', scale=alt.Scale(domain=['成功', '失敗'], range=['#00b050', '#ff4b4b']), legend=alt.Legend(title="", orient="bottom")),
        order=alt.Order('結果:N', sort='ascending'),
        tooltip=[f"{x_col}:N", '結果:N', '回数:Q']
    )
    df_text = df_m[df_m['回数'] > 0].copy()
    text = alt.Chart(df_text).mark_text(dx=0, dy=12, color='white', baseline='top', fontWeight='bold', fontSize=11).encode(
        x=alt.X(f"{x_col}:N", sort=None), y=alt.Y('回数:Q', stack='zero'), detail='結果:N', order=alt.Order('結果:N', sort='ascending'), text='回数:Q'
    )
    df_total = df_m.groupby(x_col, as_index=False)['回数'].sum()
    df_total_text = df_total[df_total['回数'] > 0].copy()
    total_text = alt.Chart(df_total_text).mark_text(dy=-8, color='black', fontWeight='bold', fontSize=12).encode(
        x=alt.X(f"{x_col}:N", sort=None), y=alt.Y('回数:Q'), text='回数:Q'
    )
    chart = alt.layer(bars, text, total_text).properties(height=250)
    st.altair_chart(chart, use_container_width=True)

def draw_simple_bar_chart(s, x_name, max_y, sort_order, color_range=None):
    if s.empty: return
    df = s.to_frame(name='回数').reset_index()
    df.columns = [x_name, '回数']
    color_encode = alt.Color(f'{x_name}:N', legend=None)
    if color_range: color_encode = alt.Color(f'{x_name}:N', scale=alt.Scale(domain=sort_order, range=color_range), legend=None)
    bars = alt.Chart(df).mark_bar().encode(
        x=alt.X(f"{x_name}:N", sort=sort_order, title='', axis=alt.Axis(labelAngle=0, labelOverlap=False)),
        y=alt.Y('回数:Q', scale=alt.Scale(domain=[0, max_y]), title=''), color=color_encode, tooltip=[f"{x_name}:N", '回数:Q']
    )
    df_text = df[df['回数'] > 0].copy()
    text = alt.Chart(df_text).mark_text(dy=-8, color='black', fontWeight='bold', fontSize=12).encode(
        x=alt.X(f"{x_name}:N", sort=sort_order), y=alt.Y('回数:Q'), text='回数:Q'
    )
    chart = alt.layer(bars, text).properties(height=200)
    st.altair_chart(chart, use_container_width=True)

def generate_coach_advice(df, home_name, away_name):
    if df.empty: return "データが十分にありません。"
    h_df = df[df['チーム'] == home_name]; a_df = df[df['チーム'] == away_name]
    if h_df.empty: return f"{home_name}のデータがありません。"
    good, bad = [], []
    h_pts = h_df['点数'].sum(); a_pts = a_df['点数'].sum()
    h_2p = h_df[h_df['項目'] == '2P']; h_2p_pct = len(h_2p[h_2p['結果']=='成功']) / len(h_2p) if len(h_2p) > 0 else 0
    h_3p = h_df[h_df['項目'] == '3P']; h_3p_pct = len(h_3p[h_3p['結果']=='成功']) / len(h_3p) if len(h_3p) > 0 else 0
    h_ft = h_df[h_df['項目'] == 'FT']; h_ft_pct = len(h_ft[h_ft['結果']=='成功']) / len(h_ft) if len(h_ft) > 0 else 0
    h_or, h_dr = len(h_df[h_df['項目'] == 'OR']), len(h_df[h_df['項目'] == 'DR'])
    a_or, a_dr = len(a_df[a_df['項目'] == 'OR']), len(a_df[a_df['項目'] == 'DR'])
    h_reb, a_reb = h_or + h_dr, a_or + a_dr
    h_ast = len(h_df[h_df['項目'] == 'AST']); h_to = len(h_df[h_df['項目'] == 'TO'])
    h_pm = len(h_df[(h_df['項目'] == 'TO') & (h_df['詳細'] == 'PM')]); h_foul = len(h_df[h_df['項目'] == 'Foul'])

    if h_3p_pct >= 0.33 and len(h_3p) >= 3: good.append(f"🎯 **外角のシュートタッチが良好！** (3P成功率: {h_3p_pct*100:.1f}%) この調子でスペーシングを広く保ちましょう。")
    if h_or > a_or and h_or >= 3: good.append(f"💪 **オフェンスリバウンドで圧倒！** ({h_or}本) 泥臭いプレイがセカンドチャンスを生んでいます。")
    if h_ast >= 5: good.append(f"🤝 **ボールがよく回っています！** ({h_ast}アシスト) 個人技に頼らない素晴らしいチームオフェンスです。")
    if not good:
        if h_pts > a_pts: good.append("🔥 **リードを保っています！** 今のリズムを崩さず、ディフェンスから速攻を狙いましょう。")
        else: good.append("🛡️ **まずはディフェンスから！** 苦しい時間帯ですが、1回のストップから流れを引き寄せましょう。")

    if h_2p_pct < 0.40 and len(h_2p) > 5: bad.append(f"⚠️ **ペイント付近のフィニッシュ精度に課題** (2P成功率: {h_2p_pct*100:.1f}%)。無理なタフショットを減らし、確実なシュートセレクションを。")
    if h_reb < a_reb: bad.append(f"⚠️ **リバウンドで劣勢です** (総数 {h_reb} 対 {a_reb})。全員で徹底したスクリーンアウト(ボックスアウト)を意識してください。")
    if h_to >= 5:
        if h_pm >= 3: bad.append(f"⚠️ **パスミス(PM)が目立ちます** ({h_pm}回)。無理なパスを避け、まずは安全なボール運びを！")
        else: bad.append(f"⚠️ **ターンオーバーが多いです** ({h_to}回)。自滅によるポゼッション献上は相手を勢いづけます。ボールを大切に。")
    if h_ft_pct < 0.60 and len(h_ft) >= 4: bad.append(f"⚠️ **フリースローを取りこぼしています** (成功率: {h_ft_pct*100:.1f}%)。ノーマークの確実な得点源です、集中して打ちましょう。")
    if h_foul >= 6: bad.append(f"⚠️ **ファウルトラブルに注意** ({h_foul}回)。不要な手を出さず、足で守るディフェンスを徹底してください。")
    if not bad: bad.append("✨ **大きな崩れはありません！** 今のプレイスタイルを継続し、さらにインテンシティを高めていきましょう。")

    html = "<div class='advice-box'><h4 style='margin-top:0;'>🟢 良かった点・継続すること</h4>"
    for g in good: html += f"<p class='advice-good'>・{g}</p>"
    html += "<h4>🔴 改善点・次への課題</h4>"
    for b in bad: html += f"<p class='advice-bad'>・{b}</p>"
    html += "</div>"
    return html

def draw_report_body():
    st.header("1. スコア推移")
    try:
        rep_qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[st.session_state.home_name, st.session_state.away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
        rep_qs['Total'] = rep_qs.sum(axis=1); st.table(rep_qs.astype(int))
    except: pass
    st.header("2. 分析グラフ")
    selected_q_graph = st.radio("グラフ対象期間", ["Total", "1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")
    if selected_q_graph == "Total": filtered_history = st.session_state.history
    else: filtered_history = st.session_state.history[st.session_state.history['Q'] == selected_q_graph]
    h_players = ["全体"] + sorted([p.replace('番','') for p in filtered_history[filtered_history['チーム']==st.session_state.home_name]['名前'].unique() if p != 'TEAM'], key=safe_sort_key)
    sel_h = st.radio(f"🔵 {st.session_state.home_name} 選手選択", h_players, horizontal=True, label_visibility="collapsed")
    a_players = ["全体"] + sorted([p.replace('番','') for p in filtered_history[filtered_history['チーム']==st.session_state.away_name]['名前'].unique() if p != 'TEAM'], key=safe_sort_key)
    sel_a = st.radio(f"🔴 {st.session_state.away_name} 選手選択", a_players, horizontal=True, label_visibility="collapsed")

    df_h_graph = filtered_history[filtered_history['チーム'] == st.session_state.home_name]
    if sel_h != "全体": df_h_graph = df_h_graph[df_h_graph['名前'] == f"{sel_h}番"]
    df_a_graph = filtered_history[filtered_history['チーム'] == st.session_state.away_name]
    if sel_a != "全体": df_a_graph = df_a_graph[df_a_graph['名前'] == f"{sel_a}番"]

    st.subheader(f"① 全体シュート ({selected_q_graph})")
    def get_shot_stats(df):
        sh = df[df['項目'].isin(['2P', '3P', 'FT'])]
        if sh.empty: return pd.DataFrame(columns=['成功', '失敗'], index=['2P', '3P', 'FT']).fillna(0)
        stats = sh.groupby(['項目', '結果']).size().unstack(fill_value=0)
        for c in ['成功', '失敗']:
            if c not in stats.columns: stats[c] = 0
        return stats[['成功', '失敗']].reindex(['2P', '3P', 'FT'], fill_value=0)
    s_stats_h = get_shot_stats(df_h_graph); s_stats_a = get_shot_stats(df_a_graph)
    max_y_overall = max(s_stats_h.sum(axis=1).max(), s_stats_a.sum(axis=1).max())
    max_y_overall = int(max_y_overall * 1.15) + 1 if max_y_overall > 0 else 5
    g1, g2 = st.columns(2)
    with g1:
        st.write(f"🔵 **{sel_h}**" if sel_h != "全体" else f"🔵 **{st.session_state.home_name}**")
        if s_stats_h.sum().sum() > 0: draw_stacked_chart(s_stats_h, '項目', max_y_overall)
        else: st.caption("データなし")
    with g2:
        st.write(f"🔴 **{sel_a}**" if sel_a != "全体" else f"🔴 **{st.session_state.away_name}**")
        if s_stats_a.sum().sum() > 0: draw_stacked_chart(s_stats_a, '項目', max_y_overall)
        else: st.caption("データなし")

    st.subheader(f"② エリア別シュート分布 ({selected_q_graph})")
    area_target = st.radio("表示項目", ["2P", "3P"], horizontal=True, label_visibility="collapsed", key="area_target_radio")
    def get_area_stats(df, target, areas_order):
        sh = df[df['項目'] == target]
        if sh.empty: return pd.DataFrame(columns=['成功', '失敗'], index=areas_order).fillna(0)
        stats = sh.groupby(['詳細', '結果']).size().unstack(fill_value=0)
        for c in ['成功', '失敗']:
            if c not in stats.columns: stats[c] = 0
        return stats[['成功', '失敗']].reindex(areas_order, fill_value=0)
    
    areas_order = ["左下", "中下", "右下", "左レ", "中レ", "右レ", "左角", "左45", "中", "右45", "右角"] if area_target == "2P" else ["左角", "左45", "中", "右45", "右角"]
    a_stats_h = get_area_stats(df_h_graph, area_target, areas_order); a_stats_a = get_area_stats(df_a_graph, area_target, areas_order)
    max_y_area = max(a_stats_h.sum(axis=1).max(), a_stats_a.sum(axis=1).max())
    max_y_area = int(max_y_area * 1.15) + 1 if max_y_area > 0 else 5
    ga1, ga2 = st.columns(2)
    with ga1:
        st.write(f"🔵 **{sel_h}**" if sel_h != "全体" else f"🔵 **{st.session_state.home_name}**")
        if a_stats_h.sum().sum() > 0: draw_stacked_chart(a_stats_h, '詳細', max_y_area)
        else: st.caption("データなし")
    with ga2:
        st.write(f"🔴 **{sel_a}**" if sel_a != "全体" else f"🔴 **{st.session_state.away_name}**")
        if a_stats_a.sum().sum() > 0: draw_stacked_chart(a_stats_a, '詳細', max_y_area)
        else: st.caption("データなし")

    st.subheader(f"③ リバウンド ({selected_q_graph})")
    def get_reb_stats(df):
        sh = df[df['項目'].isin(['OR', 'DR'])]
        if sh.empty: return pd.Series({'OR':0, 'DR':0, 'Total':0})
        stats = sh.groupby('項目').size()
        for c in ['OR', 'DR']:
            if c not in stats.index: stats[c] = 0
        s = stats[['OR', 'DR']]; s['Total'] = s.sum()
        return s
    r_stats_h = get_reb_stats(df_h_graph); r_stats_a = get_reb_stats(df_a_graph)
    max_y_reb = max(r_stats_h.max(), r_stats_a.max())
    max_y_reb = int(max_y_reb * 1.15) + 1 if max_y_reb > 0 else 5
    gr1, gr2 = st.columns(2)
    with gr1:
        st.write(f"🔵 **{sel_h}**" if sel_h != "全体" else f"🔵 **{st.session_state.home_name}**")
        if r_stats_h.sum() > 0: draw_simple_bar_chart(r_stats_h, '種類', max_y_reb, ['OR', 'DR', 'Total'], ['#ff9f43', '#3498db', '#2ecc71'])
        else: st.caption("データなし")
    with gr2:
        st.write(f"🔴 **{sel_a}**" if sel_a != "全体" else f"🔴 **{st.session_state.away_name}**")
        if r_stats_a.sum() > 0: draw_simple_bar_chart(r_stats_a, '種類', max_y_reb, ['OR', 'DR', 'Total'], ['#ff9f43', '#3498db', '#2ecc71'])
        else: st.caption("データなし")

    st.subheader(f"④ ターンオーバー ({selected_q_graph})")
    def get_to_stats(df):
        sh = df[df['項目'] == 'TO']
        to_cols = ['TV', 'DD', 'PM', '24S']
        if sh.empty: return pd.Series({c:0 for c in to_cols + ['Total']})
        stats = sh.groupby('詳細').size()
        for c in to_cols:
            if c not in stats.index: stats[c] = 0
        s = stats[to_cols]; s['Total'] = s.sum()
        return s
    to_stats_h = get_to_stats(df_h_graph); to_stats_a = get_to_stats(df_a_graph)
    max_y_to = max(to_stats_h.max(), to_stats_a.max())
    max_y_to = int(max_y_to * 1.15) + 1 if max_y_to > 0 else 5
    gt1, gt2 = st.columns(2)
    with gt1:
        st.write(f"🔵 **{sel_h}**" if sel_h != "全体" else f"🔵 **{st.session_state.home_name}**")
        if to_stats_h.sum() > 0: draw_simple_bar_chart(to_stats_h, '詳細', max_y_to, ['TV', 'DD', 'PM', '24S', 'Total'], ['#95a5a6', '#95a5a6', '#95a5a6', '#95a5a6', '#e74c3c'])
        else: st.caption("データなし")
    with gt2:
        st.write(f"🔴 **{sel_a}**" if sel_a != "全体" else f"🔴 **{st.session_state.away_name}**")
        if to_stats_a.sum() > 0: draw_simple_bar_chart(to_stats_a, '詳細', max_y_to, ['TV', 'DD', 'PM', '24S', 'Total'], ['#95a5a6', '#95a5a6', '#95a5a6', '#95a5a6', '#e74c3c'])
        else: st.caption("データなし")

    st.header("3. 個人スタッツ")
    all_h = [x.strip() for x in st.session_state.r_str_h.split(",") if x.strip()]
    all_a = [x.strip() for x in st.session_state.r_str_a.split(",") if x.strip()]

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
    st.header("4. 💡 分析結果コメント（自動アドバイス）")
    advice_html = generate_coach_advice(filtered_history, st.session_state.home_name, st.session_state.away_name)
    st.markdown(advice_html, unsafe_allow_html=True)
    st.divider()
    st.header("5. 詳細ログ")
    st.dataframe(st.session_state.history.iloc[::-1], use_container_width=True)
    csv_stats = pd.concat([h_df, a_df], ignore_index=True).to_csv(index=False).encode('utf_8_sig')
    st.download_button("📊 統計CSV保存", csv_stats, f"{st.session_state.tournament_name}_stats.csv", "text/csv")
    csv_log = st.session_state.history.to_csv(index=False).encode('utf_8_sig')
    st.download_button("📜 ログCSV保存", csv_log, f"{st.session_state.tournament_name}_log.csv", "text/csv")

if st.session_state.read_only:
    tab_report, = st.tabs(["📄 ライブ統計レポート"])
    with tab_report:
        if st.button("🔄 記録者の最新データを読み込む", use_container_width=True, type="primary"):
            if os.path.exists(LOG_FILE):
                try:
                    df = pd.read_csv(LOG_FILE)
                    df['点数'] = pd.to_numeric(df['点数'], errors='coerce').fillna(0).astype(int)
                    st.session_state.history = df
                except: pass
            if os.path.exists(SET_FILE):
                try:
                    with open(SET_FILE, "r", encoding="utf-8") as f: s = json.load(f)
                    for k, v in s.items(): st.session_state[k] = v
                except: pass
            st.session_state.report_trigger = True
            st.rerun()
        if st.session_state.history.empty: st.info("データがありません。「最新データを読み込む」ボタンを押してください。")
        elif not st.session_state.report_trigger: st.info("上のボタンを押すと最新のグラフが表示されます。")
        else: draw_report_body()

else:
    tab_input, tab_report, tab_edit = st.tabs(["✍️ 記録入力", "📄 統計レポート", "🛠 修正"])
    with tab_input:
        if not st.session_state.history.empty:
            try:
                qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[st.session_state.home_name, st.session_state.away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
                qs['Total'] = qs.sum(axis=1); st.table(qs.astype(int))
            except: pass
        
        st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed", key="current_q", on_change=safe_rerun)

        # --- HOME チーム ---
        st.write(f"🔵 **{st.session_state.home_name}**")
        if not st.session_state.act_h: st.warning("サイドバーで選手を選んでください")
        else:
            cols_h = st.columns(len(st.session_state.act_h))
            for i, p_num in enumerate(st.session_state.act_h):
                if cols_h[i].button(p_num, key=f"h_{p_num}", use_container_width=True):
                    st.session_state.tmp = {'player': p_num, 'team': st.session_state.home_name}; st.session_state.mode = "項目選択"; safe_rerun()
        if st.button(f"⏰ {st.session_state.home_name} TOUT", use_container_width=True): record("TOUT", team=st.session_state.home_name, name="TEAM"); safe_rerun()

        # --- センター固定の操作パネル ---
        if st.session_state.mode != "選手選択":
            st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
            draw_action_menu()
            st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)

        st.divider()

        # --- AWAY チーム ---
        st.write(f"🔴 **{st.session_state.away_name}**")
        if not st.session_state.act_a: st.warning("サイドバーで選手を選んでください")
        else:
            cols_a = st.columns(len(st.session_state.act_a))
            for i, p_num in enumerate(st.session_state.act_a):
                if cols_a[i].button(p_num, key=f"a_{p_num}", use_container_width=True):
                    st.session_state.tmp = {'player': p_num, 'team': st.session_state.away_name}; st.session_state.mode = "項目選択"; safe_rerun()
        if st.button(f"⏰ {st.session_state.away_name} TOUT", use_container_width=True): record("TOUT", team=st.session_state.away_name, name="TEAM"); safe_rerun()

    with tab_report:
        if st.session_state.history.empty: st.info("データなし")
        else:
            if not st.session_state.report_trigger:
                st.info("⚡ 試合中の入力スピードを最優先するため、グラフとスタッツは非表示になっています。")
                if st.button("📊 最新のデータでレポートを計算・表示する", use_container_width=True, type="primary"):
                    st.session_state.report_trigger = True
                    st.rerun()
            else: draw_report_body()
    
    with tab_edit:
        st.header("🛠 修正")
        if not st.session_state.history.empty:
            for i, row in st.session_state.history.iloc[::-1].iterrows():
                cols = st.columns([4, 1])
                cols[0].write(f"{row['Q']}|{row['名前']}|{row['項目']}({row['詳細']})")
                if cols[1].button("🗑️", key=f"del_{i}"): st.session_state.history = st.session_state.history.drop(i); safe_rerun()

if not st.session_state.read_only and st.session_state.mode in ["選手選択", "アシスト選択", "リバウンド選択"]:
    save_state()

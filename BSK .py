import streamlit as st
import pandas as pd
import io
import re
import unicodedata

# ページ設定
st.set_page_config(page_title="バスケ分析Pro V07.6", layout="centered")

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

# --- ★新規：強力な文字クリーニング関数 ---
def clean_player_text(raw_str):
    if pd.isna(raw_str): return ""
    s = str(raw_str).strip()
    # ⑧ -> 8, １３ -> 13 のように全角を半角に強制変換
    s = unicodedata.normalize('NFKC', s)
    # 英数字と日本語（漢字カナ等）以外（。、, . などの記号）をすべて削除
    s = re.sub(r'[^\w]', '', s)
    return s

def safe_sort_key(x):
    # 文字列の中から数字の部分だけを抜き出して並べ替え（エラー回避）
    m = re.search(r'\d+', str(x))
    return int(m.group()) if m else 99999

# カンマや空白、読点などでリストを分割して綺麗にする関数
def parse_roster_string(raw_str):
    raw_list = re.split(r'[,，、\s]+', str(raw_str))
    res = []
    for x in raw_list:
        c = clean_player_text(x)
        if c and c not in res:
            res.append(c)
    return sorted(res, key=safe_sort_key)

# --- 1. データ初期化 ---
if 'history' not in st.session_state: st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state: st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state: st.session_state.tmp = {}
if 'current_q' not in st.session_state: st.session_state.current_q = "1Q"

if 'team_h_name' not in st.session_state: st.session_state.team_h_name = "HOME"
if 'team_a_name' not in st.session_state: st.session_state.team_a_name = "AWAY"
if 'r_str_h' not in st.session_state: st.session_state.r_str_h = "4,5,6,7,8,9,10,11,12,13,14,15"
if 'act_h' not in st.session_state: st.session_state.act_h = ["4","5","6","7","8"]
if 'r_str_a' not in st.session_state: st.session_state.r_str_a = "4,5,6,7,8,9,10,11,12,13,14,15"
if 'act_a' not in st.session_state: st.session_state.act_a = ["4","5","6","7","8"]

# --- CSV読み込み処理 ---
def load_csv_data():
    if st.session_state.uploaded_file is not None:
        try:
            file_bytes = st.session_state.uploaded_file.getvalue()
            df = pd.read_csv(io.BytesIO(file_bytes))
            
            if set(['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数']).issubset(df.columns):
                # チーム名クリーニング
                df['チーム'] = df['チーム'].astype(str).str.strip()
                
                # ★修正：名前欄に混入した記号や⑧を完全にクリーンアップ
                def fix_csv_name(n):
                    n_str = str(n).replace('番', '').strip()
                    if n_str.upper() in ['TEAM', 'UNKNOWN', 'NAN', 'NONE', '']:
                        return 'TEAM'
                    c = clean_player_text(n_str)
                    return f"{c}番" if c else 'TEAM'
                
                df['名前'] = df['名前'].apply(fix_csv_name)
                df['項目'] = df['項目'].astype(str).str.strip()
                df['詳細'] = df['詳細'].astype(str).str.strip()
                df['結果'] = df['結果'].astype(str).str.strip()
                df['点数'] = pd.to_numeric(df['点数'], errors='coerce').fillna(0).astype(int)
                
                st.session_state.history = df
                
                teams = [t for t in df['チーム'].unique() if t and str(t).upper() != 'UNKNOWN']
                if len(teams) > 0: st.session_state.team_h_name = teams[0]
                if len(teams) > 1: st.session_state.team_a_name = teams[1]
                
                def extract_players(team_name):
                    p_list = df[df['チーム'] == team_name]['名前'].unique()
                    extracted = [str(p).replace('番', '').strip() for p in p_list if str(p).upper() not in ['TEAM', 'NAN', 'NONE']]
                    return sorted([clean_player_text(p) for p in extracted if clean_player_text(p)], key=safe_sort_key)
                
                if len(teams) > 0:
                    h_p = extract_players(teams[0])
                    if h_p:
                        # 既存と合体させる
                        curr_h = parse_roster_string(st.session_state.r_str_h)
                        merged_h = sorted(list(set(curr_h + h_p)), key=safe_sort_key)
                        st.session_state.r_str_h = ",".join(merged_h)
                        st.session_state.act_h = h_p[:5]
                if len(teams) > 1:
                    a_p = extract_players(teams[1])
                    if a_p:
                        curr_a = parse_roster_string(st.session_state.r_str_a)
                        merged_a = sorted(list(set(curr_a + a_p)), key=safe_sort_key)
                        st.session_state.r_str_a = ",".join(merged_a)
                        st.session_state.act_a = a_p[:5]
                        
                st.toast("✅ データを完全に復元しました！")
            else:
                st.error("対応していないCSV形式です。詳細ログ(.csv)を選んでください。")
        except Exception as e:
            st.error(f"読み込みエラー: {e}")

# --- 2. サイドバー ---
with st.sidebar:
    st.header("🏆 試合設定")
    tournament_name = st.text_input("大会名", "練習試合")
    st.divider()
    
    # === HOME ===
    st.text_input("自チーム名", key="team_h_name")
    
    new_h = st.text_input(f"🔵 新規選手を追加", placeholder="例: 99", key="in_h")
    if st.button("＋追加＆出場", key="add_h", use_container_width=True):
        if new_h:
            new_nums = parse_roster_string(new_h)
            all_h_list = parse_roster_string(st.session_state.r_str_h)
            for n in new_nums:
                if n not in all_h_list: all_h_list.append(n)
                if n not in st.session_state.act_h: st.session_state.act_h.append(n)
            st.session_state.r_str_h = ",".join(sorted(all_h_list, key=safe_sort_key))
            st.rerun()

    with st.expander(f"👥 {st.session_state.team_h_name} 名簿を手動編集"):
        st.session_state.r_str_h = st.text_area("全背番号 (カンマ等で区切る)", value=st.session_state.r_str_h, key="ta_h")
    
    all_h = parse_roster_string(st.session_state.r_str_h)
    valid_act_h = [x for x in st.session_state.act_h if x in all_h]
    st.session_state.act_h = st.multiselect(f"🔵 {st.session_state.team_h_name} オンコート", all_h, default=valid_act_h)
    
    st.divider()
    
    # === AWAY ===
    st.text_input("相手チーム名", key="team_a_name")
    
    new_a = st.text_input(f"🔴 新規選手を追加", placeholder="例: 99", key="in_a")
    if st.button("＋追加＆出場", key="add_a", use_container_width=True):
        if new_a:
            new_nums = parse_roster_string(new_a)
            all_a_list = parse_roster_string(st.session_state.r_str_a)
            for n in new_nums:
                if n not in all_a_list: all_a_list.append(n)
                if n not in st.session_state.act_a: st.session_state.act_a.append(n)
            st.session_state.r_str_a = ",".join(sorted(all_a_list, key=safe_sort_key))
            st.rerun()

    with st.expander(f"👥 {st.session_state.team_a_name} 名簿を手動編集"):
        st.session_state.r_str_a = st.text_area("全背番号 (カンマ等で区切る)", value=st.session_state.r_str_a, key="ta_a")
    
    all_a = parse_roster_string(st.session_state.r_str_a)
    valid_act_a = [x for x in st.session_state.act_a if x in all_a]
    st.session_state.act_a = st.multiselect(f"🔴 {st.session_state.team_a_name} オンコート", all_a, default=valid_act_a)
    
    st.divider()
    
    # --- 過去データ復元（CSV読み込み）---
    with st.expander("📂 過去データを復元・確認 (CSV読込)"):
        st.write("「詳細ログ」のCSVを選択してください。自動で読み込まれます。")
        st.file_uploader("詳細ログCSVを選択", type=["csv"], label_visibility="collapsed", key="uploaded_file", on_change=load_csv_data)
    
    st.divider()
    if st.button("全データリセット (新規試合)", type="secondary", use_container_width=True):
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
            qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[st.session_state.team_h_name, st.session_state.team_a_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            qs['Total'] = qs.sum(axis=1); st.table(qs.astype(int))
        except: pass
    st.session_state.current_q = st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")

    st.write(f"🔵 **{st.session_state.team_h_name}**")
    if not st.session_state.act_h: st.warning("サイドバーで選手を選んでください")
    else:
        cols_h = st.columns(len(st.session_state.act_h))
        for i, p_num in enumerate(st.session_state.act_h):
            if cols_h[i].button(p_num, key=f"h_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': st.session_state.team_h_name}; st.session_state.mode = "項目選択"; st.rerun()
    if st.button(f"⏰ {st.session_state.team_h_name} TOUT", use_container_width=True): record("TOUT", team=st.session_state.team_h_name, name="TEAM")

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
            
            if sc[0].button("SUCCESS", use_container_width=True, type="primary"):
                record(item, detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts)
                if item in ["2P", "3P"]: st.session_state.mode = "アシスト選択"
                st.rerun()
            if sc[1].button("MISS", use_container_width=True): 
                record(item, detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0)
                st.rerun()
            if st.button("戻る", use_container_width=True): 
                st.session_state.mode="エリア選択" if "P" in item else "項目選択"; st.rerun()

        elif st.session_state.mode == "アシスト選択":
            scorer = st.session_state.tmp.get('player')
            t_name = st.session_state.tmp.get('team')
            st.write(f"🏀 **#{scorer}** 得点！アシストは？")
            
            active_list = st.session_state.act_h if t_name == st.session_state.team_h_name else st.session_state.act_a
            assist_candidates = [p for p in active_list if p != scorer]
            
            if assist_candidates:
                ast_c = st.columns(len(assist_candidates))
                for i, p_num in enumerate(assist_candidates):
                    if ast_c[i].button(p_num, key=f"ast_{p_num}", use_container_width=True):
                        record("AST", detail=f"to #{scorer}", res="成功", pts=0, team=t_name, name=f"{p_num}番")
                        st.rerun()
            
            st.divider()
            if st.button("❌ アシストなし", use_container_width=True):
                st.session_state.mode = "選手選択"
                st.rerun()

    st.divider()
    if st.button(f"⏰ {st.session_state.team_a_name} TOUT", use_container_width=True): record("TOUT", team=st.session_state.team_a_name, name="TEAM")
    st.write(f"🔴 **{st.session_state.team_a_name}**")
    if not st.session_state.act_a: st.warning("サイドバーで選手を選んでください")
    else:
        cols_a = st.columns(len(st.session_state.act_a))
        for i, p_num in enumerate(st.session_state.act_a):
            if cols_a[i].button(p_num, key=f"a_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': st.session_state.team_a_name}; st.session_state.mode = "項目選択"; st.rerun()

# 【タブ2】レポート 
with tab_report:
    if st.session_state.history.empty: st.info("データなし")
    else:
        st.header("1. スコア推移")
        try:
            rep_qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[st.session_state.team_h_name, st.session_state.team_a_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            rep_qs['Total'] = rep_qs.sum(axis=1); st.table(rep_qs.astype(int))
        except: pass

        st.header("2. 個人スタッツ")
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
        
        st.write(f"🔵 **{st.session_state.team_h_name}**"); h_df = get_stats_df(st.session_state.team_h_name, all_h); st.table(h_df.drop(columns='Team').set_index('#'))
        st.write(f"🔴 **{st.session_state.team_a_name}**"); a_df = get_stats_df(st.session_state.team_a_name, all_a); st.table(a_df.drop(columns='Team').set_index('#'))

        st.divider()
        st.header("3. 詳細ログ")
        st.dataframe(st.session_state.history.iloc[::-1], use_container_width=True)
        
        csv_stats = pd.concat([h_df, a_df], ignore_index=True).to_csv(index=False).encode('utf_8_sig')
        st.download_button("📊 統計CSV保存", csv_stats, f"{tournament_name}_stats.csv", "text/csv")
        csv_log = st.session_state.history.to_csv(index=False).encode('utf_8_sig')
        st.download_button("📜 ログCSV保存", csv_log, f"{tournament_name}_log.csv", "text/csv")

with tab_edit:
    st.header("🛠 修正")
    if not st.session_state.history.empty:
        for i, row in st.session_state.history.iloc[::-1].iterrows():
            cols = st.columns([4, 1])
            cols[0].write(f"{row['Q']}|{row['名前']}|{row['項目']}({row['詳細']})")
            if cols[1].button("🗑️", key=f"del_{i}"):
                st.session_state.history = st.session_state.history.drop(i); st.rerun()

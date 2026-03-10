import streamlit as st
import pandas as pd

st.set_page_config(page_title="バスケ分析Pro：ミス防止レイアウト", layout="centered")

# --- 1. データ保持の設定 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state:
    st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state:
    st.session_state.tmp = {}
if 'current_q' not in st.session_state:
    st.session_state.current_q = "1Q"

# --- 2. サイドバー：設定 ---
with st.sidebar:
    st.header("📋 設定")
    game_date = st.date_input("試合日")
    home_name = st.text_input("自チーム名", "HOME")
    away_name = st.text_input("相手チーム名", "AWAY")
    if st.button("全データリセット", type="secondary"):
        st.session_state.history = pd.DataFrame(columns=['Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
        st.session_state.mode = "選手選択"
        st.rerun()

# --- 3. 共通関数 ---
def record(item, detail="-", res="成功", pts=0):
    new_row = pd.DataFrame([{
        'Q': st.session_state.current_q, 
        'チーム': st.session_state.tmp['team'], 
        '名前': st.session_state.tmp['player'], 
        '項目': item, '詳細': detail, '結果': res, '点数': pts
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.session_state.mode = "選手選択" # 記録後、初期状態へ
    st.toast(f"記録：{st.session_state.tmp['team']} {st.session_state.tmp['player']}")

# --- 4. メインタブ ---
tab_input, tab_report = st.tabs(["✍️ 記録入力", "📄 レポート"])

with tab_input:
    # クォーター選択（常に上）
    st.session_state.current_q = st.radio("Q選択", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")
    st.divider()

    # --- A. 自チーム選手 (TOP) ---
    st.write(f"🔵 **{home_name}** (選手選択)")
    h_cols = st.columns(5)
    for i in range(1, 21):
        p_label = f"{i}"
        with h_cols[(i-1) % 5]:
            if st.button(p_label, key=f"h_{i}", use_container_width=True):
                st.session_state.tmp['player'] = f"{i}番"
                st.session_state.tmp['team'] = home_name
                st.session_state.mode = "項目選択"

    # --- B. 操作パネル (MIDDLE) ---
    st.divider()
    container = st.container(border=True)
    with container:
        if st.session_state.mode == "選手選択":
            st.info("上下どちらかの選手をタップしてください")
        
        elif st.session_state.mode == "項目選択":
            st.subheader(f"⚡ {st.session_state.tmp['team']} {st.session_state.tmp['player']}")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("2P", use_container_width=True, type="primary"):
                    st.session_state.tmp['item'] = "2P"; st.session_state.mode = "エリア選択"; st.rerun()
            with c2:
                if st.button("3P", use_container_width=True, type="primary"):
                    st.session_state.tmp['item'] = "3P"; st.session_state.mode = "エリア選択"; st.rerun()
            with c3:
                if st.button("FT", use_container_width=True):
                    st.session_state.tmp['item'] = "FT"; st.session_state.mode = "結果選択"; st.rerun()
            
            # その他プレイ
            o1, o2, o3, o4 = st.columns(4)
            with o1: 
                if st.button("OR", use_container_width=True): record("OR")
                if st.button("DR", use_container_width=True): record("DR")
            with o2: 
                if st.button("AST", use_container_width=True): record("AST")
                if st.button("STL", use_container_width=True): record("STL")
            with o3: 
                if st.button("F", use_container_width=True): record("Foul")
                if st.button("BLK", use_container_width=True): record("BLK")
            with o4:
                if st.button("TV", use_container_width=True): record("TO", "TV")
                if st.button("DD", use_container_width=True): record("TO", "DD")
                if st.button("PM", use_container_width=True): record("TO", "PM")
            if st.button("× 取消", use_container_width=True): st.session_state.mode = "選手選択"; st.rerun()

        elif st.session_state.mode == "エリア選択":
            st.write(f"📍 エリア選択 ({st.session_state.tmp['item']})")
            if st.session_state.tmp['item'] == "2P":
                areas = ["右ゴール下", "中ゴール下", "左ゴール下", "右レイアップ", "中レイアップ", "左レイアップ", "右コーナ", "右45deg", "中", "左45deg", "左コーナ"]
            else:
                areas = ["右コーナ3P", "右45deg3P", "中3P", "左45deg3P", "左コーナ3P"]
            
            a_cols = st.columns(2)
            for i, a in enumerate(areas):
                with a_cols[i % 2]:
                    if st.button(a, use_container_width=True):
                        st.session_state.tmp['area'] = a; st.session_state.mode = "結果選択"; st.rerun()
            if st.button("← 戻る"): st.session_state.mode = "項目選択"; st.rerun()

        elif st.session_state.mode == "結果選択":
            st.write(f"🎯 結果 ({st.session_state.tmp.get('area', 'FT')})")
            sc, fl = st.columns(2)
            pts = {"2P": 2, "3P": 3, "FT": 1}[st.session_state.tmp['item']]
            with sc:
                if st.button("SUCCESS", use_container_width=True, type="primary"):
                    record(st.session_state.tmp['item'], detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts); st.rerun()
            with fl:
                if st.button("MISS", use_container_width=True):
                    record(st.session_state.tmp['item'], detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0); st.rerun()
            if st.button("← 戻る"): st.session_state.mode = "項目選択"; st.rerun()

    st.divider()

    # --- C. 相手チーム選手 (BOTTOM) ---
    st.write(f"🔴 **{away_name}** (選手選択)")
    a_cols = st.columns(5)
    for i in range(1, 21):
        p_label = f"{i}"
        with a_cols[(i-1) % 5]:
            if st.button(p_label, key=f"a_{i}", use_container_width=True):
                st.session_state.tmp['player'] = f"{i}番"
                st.session_state.tmp['team'] = away_name
                st.session_state.mode = "項目選択"

# --- 5. レポートタブ (簡略化して表示) ---
with tab_report:
    if st.session_state.history.empty:
        st.info("データなし")
    else:
        st.title("📄 GAME REPORT")
        # 簡易スコアボード
        score = st.session_state.history.groupby('チーム')['点数'].sum()
        st.metric(f"{home_name} TOTAL", f"{int(score.get(home_name, 0))} pts")
        st.metric(f"{away_name} TOTAL", f"{int(score.get(away_name, 0))} pts")
        st.divider()
        st.write("詳細ログ")
        st.dataframe(st.session_state.history, use_container_width=True)

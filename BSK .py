import streamlit as st
import pandas as pd

st.set_page_config(page_title="バスケ分析Pro", layout="centered")

# --- 1. データ保持の設定 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['大会名', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state:
    st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state:
    st.session_state.tmp = {}
if 'current_q' not in st.session_state:
    st.session_state.current_q = "1Q"

# --- 2. サイドバー：詳細設定 ---
with st.sidebar:
    st.header("🏆 試合・チーム設定")
    tournament_name = st.text_input("大会名", "練習試合")
    game_date = st.date_input("試合日")
    
    st.divider()
    home_name = st.text_input("自チーム名", "HOME")
    default_nums = ",".join([str(i) for i in range(4, 24)])
    home_players_input = st.text_area("自チーム背番号", default_nums)
    home_players = [n.strip() for n in home_players_input.split(",") if n.strip()]

    st.divider()
    away_name = st.text_input("相手チーム名", "AWAY")
    away_players_input = st.text_area("相手チーム背番号", default_nums)
    away_players = [n.strip() for n in away_players_input.split(",") if n.strip()]

    if st.button("全データをリセット", type="secondary"):
        st.session_state.history = pd.DataFrame(columns=['大会名', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
        st.session_state.mode = "選手選択"
        st.rerun()

# --- 3. 共通記録関数 ---
def record(item, detail="-", res="成功", pts=0):
    if 'player' not in st.session_state.tmp: return
    new_row = pd.DataFrame([{
        '大会名': tournament_name, 'Q': st.session_state.current_q, 
        'チーム': st.session_state.tmp['team'], '名前': f"{st.session_state.tmp['player']}番", 
        '項目': item, '詳細': detail, '結果': res, '点数': pts
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.session_state.mode = "選手選択"
    st.toast(f"記録完了")

# --- 4. メインタブ ---
tab_input, tab_report = st.tabs(["✍️ 記録入力", "📄 最終レポート"])

with tab_input:
    # --- ① リアルタイム・スコアボード ---
    if not st.session_state.history.empty:
        try:
            scores = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0)
            q_order = ["1Q", "2Q", "3Q", "4Q", "OT"]
            scores = scores.reindex(columns=q_order, fill_value=0)
            scores['Total'] = scores.sum(axis=1)
            st.table(scores)
        except:
            pass
    
    st.session_state.current_q = st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")
    st.divider()

    # --- 自チーム選手 (TOP) ---
    st.write(f"🔵 **{home_name}**")
    h_cols = st.columns(5)
    for i, p_num in enumerate(home_players):
        with h_cols[i % 5]:
            if st.button(p_num, key=f"h_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': home_name}
                st.session_state.mode = "項目選択"

    # --- 操作パネル (MIDDLE) ---
    st.divider()
    with st.container(border=True):
        if st.session_state.mode == "選手選択":
            st.info("選手をタップして開始")
        
        elif st.session_state.mode == "項目選択":
            st.subheader(f"⚡ {st.session_state.tmp.get('team')} #{st.session_state.tmp.get('player')}")
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
            
            o_cols = st.columns(4)
            with o_cols[0]:
                if st.button("OR", use_container_width=True): record("OR")
                if st.button("DR", use_container_width=True): record("DR")
            with o_cols[1]:
                if st.button("AST", use_container_width=True): record("AST")
                if st.button("STL", use_container_width=True): record("STL")
            with o_cols[2]:
                if st.button("F", use_container_width=True): record("Foul")
                if st.button("BLK", use_container_width=True): record("BLK")
            with o_cols[3]:
                if st.button("TV", use_container_width=True): record("TO", "TV")
                if st.button("DD", use_container_width=True): record("TO", "DD")
                if st.button("PM", use_container_width=True): record("TO", "PM")
            if st.button("キャンセル", use_container_width=True): st.session_state.mode = "選手選択"; st.rerun()

        elif st.session_state.mode == "エリア選択":
            item_type = st.session_state.tmp.get('item', '2P')
            st.write(f"📍 エリア選択 ({item_type})")
            
            if item_type == "2P":
                # --- 2P: 3-3-5 配列 ---
                # 1段目: ゴール下 (左・中・右)
                r1 = st.columns(3)
                if r1[0].button("左ゴール下", use_container_width=True): st.session_state.tmp['area']="左ゴール下"; st.session_state.mode="結果選択"; st.rerun()
                if r1[1].button("中ゴール下", use_container_width=True): st.session_state.tmp['area']="中ゴール下"; st.session_state.mode="結果選択"; st.rerun()
                if r1[2].button("右ゴール下", use_container_width=True): st.session_state.tmp['area']="右ゴール下"; st.session_state.mode="結果選択"; st.rerun()
                # 2段目: レイアップ (左・中・右)
                r2 = st.columns(3)
                if r2[0].button("左レイアップ", use_container_width=True): st.session_state.tmp['area']="左レイアップ"; st.session_state.mode="結果選択"; st.rerun()
                if r2[1].button("中レイアップ", use_container_width=True): st.session_state.tmp['area']="中レイアップ"; st.session_state.mode="結果選択"; st.rerun()
                if r2[2].button("右レイアップ", use_container_width=True): st.session_state.tmp['area']="右レイアップ"; st.session_state.mode="結果選択"; st.rerun()
                # 3段目: その他 (左角・左45・中・右45・右角)
                r3 = st.columns(5)
                if r3[0].button("左コーナ", use_container_width=True): st.session_state.tmp['area']="左コーナ"; st.session_state.mode="結果選択"; st.rerun()
                if r3[1].button("左45deg", use_container_width=True): st.session_state.tmp['area']="左45deg"; st.session_state.mode="結果選択"; st.rerun()
                if r3[2].button("中", use_container_width=True): st.session_state.tmp['area']="中"; st.session_state.mode="結果選択"; st.rerun()
                if r3[3].button("右45deg", use_container_width=True): st.session_state.tmp['area']="右45deg"; st.session_state.mode="結果選択"; st.rerun()
                if r3[4].button("右コーナ", use_container_width=True): st.session_state.tmp['area']="右コーナ"; st.session_state.mode="結果選択"; st.rerun()
            else:
                # --- 3P: 5枚配列 ---
                r4 = st.columns(5)
                if r4[0].button("左角3P", use_container_width=True): st.session_state.tmp['area']="左コーナ3P"; st.session_state.mode="結果選択"; st.rerun()
                if r4[1].button("左45 3P", use_container_width=True): st.session_state.tmp['area']="左45deg3P"; st.session_state.mode="結果選択"; st.rerun()
                if r4[2].button("中 3P", use_container_width=True): st.session_state.tmp['area']="中3P"; st.session_state.mode="結果選択"; st.rerun()
                if r4[3].button("右45 3P", use_container_width=True): st.session_state.tmp['area']="右45deg3P"; st.session_state.mode="結果選択"; st.rerun()
                if r4[4].button("右角3P", use_container_width=True): st.session_state.tmp['area']="右コーナ3P"; st.session_state.mode="結果選択"; st.rerun()
            
            if st.button("戻る"): st.session_state.mode = "項目選択"; st.rerun()

        elif st.session_state.mode == "結果選択":
            st.write(f"🎯 結果 ({st.session_state.tmp.get('area', 'FT')})")
            sc, fl = st.columns(2)
            pts = {"2P": 2, "3P": 3, "FT": 1}.get(st.session_state.tmp.get('item'), 0)
            with sc:
                if st.button("SUCCESS", use_container_width=True, type="primary"):
                    record(st.session_state.tmp['item'], detail=st.session_state.tmp.get('area','-'), res="成功", pts=pts); st.rerun()
            with fl:
                if st.button("MISS", use_container_width=True):
                    record(st.session_state.tmp['item'], detail=st.session_state.tmp.get('area','-'), res="失敗", pts=0); st.rerun()
            if st.button("戻る"): st.session_state.mode = "エリア選択" if "P" in st.session_state.tmp['item'] else "項目選択"; st.rerun()

    st.divider()

    # --- 相手チーム選手 (BOTTOM) ---
    st.write(f"🔴 **{away_name}**")
    a_cols = st.columns(5)
    for i, p_num in enumerate(away_players):
        with a_cols[i % 5]:
            if st.button(p_num, key=f"a_{p_num}", use_container_width=True):
                st.session_state.tmp = {'player': p_num, 'team': away_name}
                st.session_state.mode = "項目選択"

# --- 【タブ2】最終レポート画面 ---
with tab_report:
    if st.session_state.history.empty:
        st.info("データなし")
    else:
        st.title(f"📊 {tournament_name} レポート")
        st.write("レポートの詳細はここから確認・印刷できます。")
        st.table(st.session_state.history.tail(10)) # 簡易表示

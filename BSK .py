import streamlit as st
import pandas as pd

st.set_page_config(page_title="バスケ記録くんPro", layout="centered")

# --- 1. データの保存場所 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['名前', '項目', 'エリア', '結果', '点数'])
if 'selected_player' not in st.session_state:
    st.session_state.selected_player = None
if 'mode' not in st.session_state:
    st.session_state.mode = "通常"
if 'temp_area' not in st.session_state:
    st.session_state.temp_area = None

PLAYERS = [f"{i}番" for i in range(1, 21)]

# --- 2. 記録用関数 ---
def record(item, area="-", result="成功", pts=0):
    new_data = pd.DataFrame([{
        '名前': st.session_state.selected_player,
        '項目': item,
        'エリア': area,
        '結果': result,
        '点数': pts
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_data], ignore_index=True)
    st.session_state.mode = "通常"
    st.session_state.temp_area = None
    st.toast(f"{st.session_state.selected_player}: {item} を記録しました！")

# --- UI部分 ---
st.title("🏀 記録くん：タップ入力")

# 選手選択
st.write("### ① 選手を選択")
p_cols = st.columns(4)
for i, p in enumerate(PLAYERS):
    with p_cols[i % 4]:
        type_btn = "primary" if st.session_state.selected_player == p else "secondary"
        if st.button(p, key=f"btn_{p}", use_container_width=True, type=type_btn):
            st.session_state.selected_player = p
            st.session_state.mode = "通常"

if st.session_state.selected_player:
    st.divider()
    st.subheader(f"現在：{st.session_state.selected_player}番")

    # --- モード1：通常（項目選択） ---
    if st.session_state.mode == "通常":
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🎯 シュート(2P/3P)", use_container_width=True, type="primary"):
                st.session_state.mode = "場所選択"; st.rerun()
        with c2:
            if st.button("⚪ フリースロー", use_container_width=True):
                st.session_state.mode = "FT結果選択"; st.rerun()
        
        # ⚠️ ファールボタンを大きく配置（間違いにくいように少し色を変える）
        if st.button("🚨 ファールを記録する", use_container_width=True):
            record("ファール")
        
        st.write("その他プレイ")
        c3, c4, c5 = st.columns(3)
        with c3:
            if st.button("OR (オフェンス)", use_container_width=True): record("OR")
            if st.button("DR (ディフェンス)", use_container_width=True): record("DR")
        with c4:
            if st.button("アシスト", use_container_width=True): record("AST")
            if st.button("スティール", use_container_width=True): record("STL")
        with c5:
            if st.button("TO (ミス)", use_container_width=True): record("TO")
            if st.button("ブロック", use_container_width=True): record("BLK")

    # --- モード：場所選択 / 結果選択 --- (前回と同じ)
    elif st.session_state.mode == "場所選択":
        st.write("### ② どこで打った？")
        m1, m2, m3 = st.columns(3)
        with m2: 
            if st.button("ゴール下", use_container_width=True): 
                st.session_state.temp_area = "ゴール下"; st.session_state.mode = "結果選択"; st.rerun()
        l, c, r = st.columns(3)
        with l: 
            if st.button("左ウィング(3P)", use_container_width=True): 
                st.session_state.temp_area = "左3P"; st.session_state.mode = "結果選択"; st.rerun()
        with c: 
            if st.button("ペイント内", use_container_width=True): 
                st.session_state.temp_area = "ペイント"; st.session_state.mode = "結果選択"; st.rerun()
        with r: 
            if st.button("右ウィング(3P)", use_container_width=True): 
                st.session_state.temp_area = "右3P"; st.session_state.mode = "結果選択"; st.rerun()
        if st.button("キャンセル", use_container_width=True): st.session_state.mode = "通常"; st.rerun()

    elif st.session_state.mode == "結果選択":
        st.write(f"### ③ 結果は？ ({st.session_state.temp_area})")
        sc, fl = st.columns(2)
        pts_val = 3 if "3P" in st.session_state.temp_area else 2
        with sc:
            if st.button(f"✅ 成功 ({pts_val}点)", use_container_width=True, type="primary"):
                record("シュート", area=st.session_state.temp_area, result="成功", pts=pts_val); st.rerun()
        with fl:
            if st.button("❌ 失敗", use_container_width=True):
                record("シュート", area=st.session_state.temp_area, result="失敗", pts=0); st.rerun()

    elif st.session_state.mode == "FT結果選択":
        st.write("### フリースローの結果")
        f1, f2 = st.columns(2)
        with f1:
            if st.button("✅ FT成功", use_container_width=True, type="primary"): record("FT", result="成功", pts=1); st.rerun()
        with f2:
            if st.button("❌ FT失敗", use_container_width=True): record("FT", result="失敗", pts=0); st.rerun()

# --- 履歴と集計 ---
st.divider()
st.write("### 🕒 直近の記録")
st.table(st.session_state.history.tail(5))

if st.button("直前の1件を消す"):
    st.session_state.history = st.session_state.history[:-1]
    st.rerun()

# --- 重要：ファール数を含む個人スタッツ表 ---
if st.checkbox("選手別の集計を表示（ファール数など）"):
    if not st.session_state.history.empty:
        # 項目ごとに個数をカウント
        summary = st.session_state.history.pivot_table(
            index='名前', 
            columns='項目', 
            aggfunc='size', 
            fill_value=0
        )
        # 合計得点の計算
        pts_summary = st.session_state.history.groupby('名前')['点数'].sum()
        summary['合計得点'] = pts_summary
        
        # ファール数が多い選手を強調したい場合は、ここを確認
        st.write("※ファールが4回以上の選手は注意！")
        st.dataframe(summary)

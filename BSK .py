import streamlit as st
import pandas as pd

st.set_page_config(page_title="本格バスケスタッツ", layout="wide")
st.title("🏀 高機能バスケ試合分析システム")

# --- 1. メンバーリスト設定 ---
HOME_TEAM = "自チーム"
AWAY_TEAM = "相手チーム"
PLAYERS = [f"選手 {i}" for i in range(1, 21)]

# --- 2. データ保存場所の初期化 ---
if 'stats_data' not in st.session_state:
    st.session_state.stats_data = pd.DataFrame(
        columns=['チーム', '選手名', 'シュートエリア', '結果', 'FT成功', 'FT試投', 'OR', 'DR', 'アシスト', 'スティール', 'TO']
    )

# --- 3. サイドバー：入力エリア ---
with st.sidebar:
    st.header("📊 スタッツ記録")
    team = st.radio("チーム", [HOME_TEAM, AWAY_TEAM])
    player = st.selectbox("選手", PLAYERS)
    
    st.divider()
    
    # シュート記録セクション
    st.subheader("🎯 シュート記録")
    area = st.selectbox("エリア", ["ゴール下", "ペイント内", "フリースローライン付近", "左ウィング", "右ウィング", "左コーナー", "右コーナー", "トップ"])
    shot_result = st.radio("結果", ["成功", "失敗"], horizontal=True)
    
    if st.button("シュートを記録"):
        new_data = pd.DataFrame([[team, player, area, shot_result, 0, 0, 0, 0, 0, 0, 0]], columns=st.session_state.stats_data.columns)
        st.session_state.stats_data = pd.concat([st.session_state.stats_data, new_data], ignore_index=True)
        st.success("シュートを保存しました")

    st.divider()
    
    # その他スタッツセクション
    st.subheader("📈 その他項目")
    stat_type = st.selectbox("項目を選択", ["フリースロー成功", "フリースロー失敗", "オフェンスリバウンド", "ディフェンスリバウンド", "アシスト", "スティール", "ターンオーバー"])
    
    if st.button("この項目を+1する"):
        # 初期値ALL0のデータを作成
        row = [team, player, "その他", "なし", 0, 0, 0, 0, 0, 0, 0]
        # 選択された項目だけ1にする
        idx = ["フリースロー成功", "フリースロー失敗", "オフェンスリバウンド", "ディフェンスリバウンド", "アシスト", "スティール", "ターンオーバー"].index(stat_type)
        if idx == 0: row[4], row[5] = 1, 1 # FT成功
        elif idx == 1: row[5] = 1          # FT試投のみ
        else: row[idx + 4] = 1             # その他(OR, DR, Ast, ST, TO)
        
        new_data = pd.DataFrame([row], columns=st.session_state.stats_data.columns)
        st.session_state.stats_data = pd.concat([st.session_state.stats_data, new_data], ignore_index=True)
        st.toast(f"{stat_type} を記録しました！")

# --- 4. メイン画面：分析表示 ---
st.header("📋 試合速報・集計")

def show_team_stats(team_name):
    df = st.session_state.stats_data[st.session_state.stats_data['チーム'] == team_name]
    if not df.empty:
        # 選手ごとに集計
        summary = df.groupby('選手名').sum(numeric_only=True)
        # シュート成功数を計算（得点計算用：3Pは簡略化して一律2点計算、後で調整可）
        success_shots = df[df['結果'] == '成功'].groupby('選手名').size()
        summary['得点'] = (success_shots * 2).fillna(0) + summary['FT成功']
        summary['REB合計'] = summary['OR'] + summary['DR']
        
        st.write(f"### {team_name} の集計")
        st.dataframe(summary[['得点', 'OR', 'DR', 'REB合計', 'アシスト', 'スティール', 'TO', 'FT成功', 'FT試投']])
        
        st.write("#### エリア別シュート成功数")
        shot_map = df[df['結果'] == '成功'].groupby('シュートエリア').size()
        st.bar_chart(shot_map)
    else:
        st.info(f"{team_name} のデータはまだありません")

col_h, col_a = st.columns(2)
with col_h: show_team_stats(HOME_TEAM)
with col_a: show_team_stats(AWAY_TEAM)

if st.button("全データをクリア"):
    st.session_state.stats_data = pd.DataFrame(columns=st.session_state.stats_data.columns)
    st.rerun()

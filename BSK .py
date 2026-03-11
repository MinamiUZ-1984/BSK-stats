import streamlit as st
import pandas as pd
from fpdf import FPDF # PDF作成用ライブラリ

# ページ設定
st.set_page_config(page_title="バスケ分析Pro - レポート完結版", layout="centered")

# --- 1. データ初期化 ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
if 'mode' not in st.session_state: st.session_state.mode = "選手選択"
if 'tmp' not in st.session_state: st.session_state.tmp = {}
if 'current_q' not in st.session_state: st.session_state.current_q = "1Q"
if 'memo' not in st.session_state: st.session_state.memo = ""

# --- 2. サイドバー設定 ---
with st.sidebar:
    st.header("🏆 試合・チーム設定")
    tournament_name = st.text_input("大会名", "練習試合")
    game_date = st.date_input("試合日")
    st.divider()
    home_name = st.text_input("自チーム名", "HOME").strip()
    home_players = [n.strip() for n in st.text_area("自チーム背番号", ",".join([str(i) for i in range(4, 24)])).split(",") if n.strip()]
    st.divider()
    away_name = st.text_input("相手チーム名", "AWAY").strip()
    away_players = [n.strip() for n in st.text_area("相手チーム背番号", ",".join([str(i) for i in range(4, 24)])).split(",") if n.strip()]
    st.divider()
    st.session_state.memo = st.text_area("コーチメモ", st.session_state.memo)
    if st.button("全データをリセット", type="secondary"):
        st.session_state.history = pd.DataFrame(columns=['id', 'Q', 'チーム', '名前', '項目', '詳細', '結果', '点数'])
        st.session_state.mode = "選手選択"
        st.rerun()

# --- 3. 記録関数 ---
def record(item, detail="-", res="成功", pts=0):
    if 'player' not in st.session_state.tmp: return
    new_id = st.session_state.history['id'].max() + 1 if not st.session_state.history.empty else 1
    new_row = pd.DataFrame([{'id': new_id, 'Q': st.session_state.current_q, 'チーム': st.session_state.tmp['team'], '名前': f"{st.session_state.tmp['player']}番", '項目': item, '詳細': detail, '結果': res, '点数': pts}])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
    st.session_state.mode = "選手選択"; st.toast(f"記録完了")

# --- 4. メインタブ ---
tab_input, tab_report, tab_edit = st.tabs(["✍️ 記録入力", "📄 分析レポート", "🛠 記録修正"])

# --- 【タブ1】入力画面 ---
with tab_input:
    if not st.session_state.history.empty:
        try:
            qs_table = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[home_name, away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
            qs_table['Total'] = qs_table.sum(axis=1); st.table(qs_table.astype(int))
        except: pass
    st.session_state.current_q = st.radio("Q", ["1Q", "2Q", "3Q", "4Q", "OT"], horizontal=True, label_visibility="collapsed")
    st.divider()
    st.write(f"🔵 **{home_name}**")
    h_cols = st.columns(5)
    for i, p_num in enumerate(home_players):
        if h_cols[i % 5].button(p_num, key=f"h_{p_num}", use_container_width=True):
            st.session_state.tmp = {'player': p_num, 'team': home_name}; st.session_state.mode = "項目選択"
    st.divider()
    with st.container(border=True):
        if st.session_state.mode == "選手選択": st.info("選手をタップしてください")
        elif st.session_state.mode == "項目選択":
            st.subheader(f"⚡ {st.session_state.tmp.get('team')} #{st.session_state.tmp.get('player')}")
            c1, c2, c3 = st.columns(3)
            if c1.button("2P", use_container_width=True, type="primary"): st.session_state.tmp['item']="2P"; st.session_state.mode="エリア選択"; st.rerun()
            if c2.button("3P", use_container_width=True, type="primary"): st.session_state.tmp['item']="3P"; st.session_state.mode="エリア選択"; st.rerun()
            if c3.button("FT", use_container_width=True): st.session_state.tmp['item']="FT"; st.session_state.mode="結果選択"; st.rerun()
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
    st.divider(); st.write(f"🔴 **{away_name}**")
    a_cols = st.columns(5)
    for i, p_num in enumerate(away_players):
        if a_cols[i % 5].button(p_num, key=f"a_{p_num}", use_container_width=True):
            st.session_state.tmp = {'player': p_num, 'team': away_name}; st.session_state.mode = "項目選択"

# --- 【タブ2】分析レポート ---
with tab_report:
    if st.session_state.history.empty:
        st.info("データなし")
    else:
        # ヘッダーとPDFボタンを横並びに
        head_l, head_r = st.columns([4, 1])
        with head_l:
            st.title(f"📊 {tournament_name}")
            st.caption(f"{game_date} | {home_name} vs {away_name}")
        with head_r:
            # PDF生成ロジック（簡易版）
            if st.button("📄 PDF生成ガイド"):
                st.info("💡 最も綺麗なPDFを作成するには：\n\n1. この画面を表示したまま **Ctrl + P** (MacはCmd+P) を押す\n2. 送信先を『PDFに保存』にする\n3. 『保存』を押す\n\n※これで表やグラフが全て反映された高品質レポートになります。")

        # 1. スコアサマリー
        st.header("1. スコア推移")
        rep_qs = st.session_state.history.groupby(['チーム', 'Q'])['点数'].sum().unstack(fill_value=0).reindex(index=[home_name, away_name], columns=["1Q", "2Q", "3Q", "4Q", "OT"], fill_value=0)
        rep_qs['Total'] = rep_qs.sum(axis=1); st.table(rep_qs.astype(int))

        # 2. 個人スタッツ + MVP
        st.header("2. 個人スタッツ")
        def build_box(t_name):
            df = st.session_state.history[st.session_state.history['チーム'] == t_name]
            if df.empty: return
            p_list = sorted(df['名前'].unique(), key=lambda x: int(x.replace('番','')) if x.replace('番','').isdigit() else 0)
            rows = []
            for p in p_list:
                pdf = df[df['名前'] == p]
                m2in, m2at = len(pdf[(pdf['項目']=='2P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='2P'])
                m3in, m3at = len(pdf[(pdf['項目']=='3P') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='3P'])
                ftin, ftat = len(pdf[(pdf['項目']=='FT') & (pdf['結果']=='成功')]), len(pdf[pdf['項目']=='FT'])
                pts, reb, ast, stl, to = pdf['点数'].sum(), len(pdf[pdf['項目'].isin(['OR','DR'])]), len(pdf[pdf['項目']=='AST']), len(pdf[pdf['項目']=='STL']), len(pdf[pdf['項目']=='TO'])
                eff = pts + reb + ast + stl - to
                rows.append({'No.': p, 'PTS': pts, 'FG': f"{m2in+m3in}-{m2at+m3at}", '3P': f"{m3in}-{m3at}", 'FT': f"{ftin}-{ftat}", 'REB': reb, 'AST': ast, 'STL': stl, 'F': len(pdf[pdf['項目']=='Foul']), 'TO': to, '_eff': eff})
            box_df = pd.DataFrame(rows); max_eff = box_df['_eff'].max(); box_df['MVP'] = box_df['_eff'].apply(lambda x: "👑" if x == max_eff and x > 0 else "")
            st.write(f"### {t_name}")
            st.dataframe(box_df[['MVP', 'No.', 'PTS', 'FG', '3P', 'FT', 'REB', 'AST', 'STL', 'F', 'TO']].set_index('No.'), use_container_width=True)
        build_box(home_name); build_box(away_name)

        # 3. シュート分析
        st.header("3. シュートエリア分析")
        shot_df = st.session_state.history[st.session_state.history['項目'].isin(['2P', '3P'])]
        if not shot_df.empty:
            area_stats = shot_df.groupby(['詳細', '結果']).size().unstack(fill_value=0)
            for c in ['成功', '失敗']: 
                if c not in area_stats.columns: area_stats[c] = 0
            area_stats['成功率%'] = (area_stats['成功'] / (area_stats['成功'] + area_stats['失敗']) * 100).round(1)
            st.bar_chart(area_stats['成功率%']); st.table(area_stats[['成功', '失敗', '成功率%']])

        if st.session_state.memo: st.info(f"📝 **コーチメモ:**\n{st.session_state.memo}")
        st.header("4. 詳細ログ")
        st.dataframe(st.session_state.history.iloc[::-1], use_container_width=True)
        csv_data = st.session_state.history.to_csv(index=False).encode('utf_8_sig')
        st.download_button("📊 レポートをCSVでダウンロード", csv_data, f"{tournament_name}_report.csv", "text/csv")

# --- 【タブ3】記録修正 ---
with tab_edit:
    st.header("🛠 修正・削除")
    if st.session_state.history.empty: st.write("データなし")
    else:
        for i, row in st.session_state.history.iloc[::-1].iterrows():
            cols = st.columns([1, 4, 1])
            cols[0].write(f"#{row.get('id', i)}")
            cols[1].write(f"{row['Q']} | {row['名前']} | {row['項目']}({row['詳細']}) | {row['結果']}")
            if cols[2].button("🗑️", key=f"del_{row.get('id', i)}"):
                st.session_state.history = st.session_state.history.drop(i); st.rerun()

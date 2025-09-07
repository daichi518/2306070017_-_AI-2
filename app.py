# app.py
import streamlit as st
import pandas as pd
from review_analysis.sentiment import analyze_text_sentences, simple_japanese_sentiment
from review_analysis.category import categorize_sentences_by_topic, TOPICS
from storage import init_storage, append_record, load_records
from datetime import datetime
import io
import json

st.set_page_config(page_title="飲食レビュー解析アプリ", layout="wide")
st.title("🍽️ 飲食レビュー解析アプリ — カテゴリ別感情解析（学籍:2306070017 中嶋大地）")
st.caption("入力されたレビューを「味／接客／雰囲気／待ち時間／価格／清潔感」に分類し、カテゴリごとの感情傾向を可視化します。APIキー不要。")

# 初期化（CSV簡易DB）
init_storage()

st.sidebar.header("操作")
mode = st.sidebar.radio("入力方法", ["テキスト入力", "ファイルアップロード（.txt/.csv）", "サンプルデータで実験"])
save_to_db = st.sidebar.checkbox("解析結果を保存（CSVに追加）", value=True)
show_saved = st.sidebar.button("保存データを表示")

st.markdown("---")
st.subheader("レビュー入力")

raw_texts = []

if mode == "テキスト入力":
    txt = st.text_area("レビューを1件ずつ改行で入力してください（例：美味しかった！でも接客が遅かった）", height=200)
    if txt.strip():
        raw_texts = [s.strip() for s in txt.splitlines() if s.strip()]

elif mode == "ファイルアップロード（.txt/.csv）":
    uploaded = st.file_uploader("ファイルを選択 (.txt / .csv)", type=["txt", "csv"])
    if uploaded:
        if uploaded.name.lower().endswith(".txt"):
            content = uploaded.read().decode("utf-8", errors="ignore")
            raw_texts = [s.strip() for s in content.splitlines() if s.strip()]
        else:
            df = pd.read_csv(uploaded, dtype=str, keep_default_na=False)
            # テキストらしき列を1つ自動選択（最初のobject列）
            text_cols = [c for c in df.columns if df[c].dtype == object]
            if text_cols:
                col = text_cols[0]
            else:
                col = df.columns[0]
            raw_texts = [str(x).strip() for x in df[col].tolist() if str(x).strip()]

else:
    # サンプルデータ
    sample = [
        "パスタがとてもおいしかった、ソースが濃厚で満足です。",
        "スタッフの対応が遅くて残念。注文から提供まで時間がかかった。",
        "店内は落ち着いた雰囲気でデートに向いていると思います。",
        "値段が高めに感じたが、量は十分だった。",
        "テーブルが少し汚れていた。清潔感がもう少し欲しい。"
    ]
    st.write("サンプルレビュー（編集可）")
    txt = st.text_area("", value="\n".join(sample), height=200)
    raw_texts = [s.strip() for s in txt.splitlines() if s.strip()]

if raw_texts:
    st.info(f"レビュー数: {len(raw_texts)} 件")
    if st.button("解析開始"):
        # 1) 文単位で分割・文ごとに感情スコア（英日対応の簡易実装）
        sentences_info = analyze_text_sentences(raw_texts)  # list of dicts: {text, lang, scores}
        # 2) カテゴリ割当（味・接客など）
        categorized = categorize_sentences_by_topic(sentences_info)

        # まとめ：カテゴリごとのスコア集計
        cat_rows = []
        for topic in TOPICS:
            sents = categorized.get(topic, [])
            if not sents:
                cat_rows.append({"topic": topic, "count": 0, "avg_compound": None, "positive_pct": None})
                continue
            comps = [s["scores"]["compound"] for s in sents]
            pos_cnt = sum(1 for s in sents if s["scores"]["compound"] > 0.05)
            avg = sum(comps)/len(comps)
            cat_rows.append({"topic": topic, "count": len(sents), "avg_compound": round(avg, 3), "positive_pct": round(pos_cnt/len(sents)*100, 1)})

        df_summary = pd.DataFrame(cat_rows)
        st.subheader("カテゴリ別集計（score: compound）")
        st.dataframe(df_summary)

        # 詳細表示エリア
        st.subheader("文ごとの解析結果（カテゴリ／言語／感情スコア）")
        detail_rows = []
        for topic, sents in categorized.items():
            for s in sents:
                detail_rows.append({
                    "category": topic,
                    "sentence": s["text"],
                    "lang": s.get("lang", "ja"),
                    "compound": s["scores"]["compound"],
                    "pos": s["scores"]["pos"],
                    "neu": s["scores"]["neu"],
                    "neg": s["scores"]["neg"]
                })
        df_detail = pd.DataFrame(detail_rows)
        st.dataframe(df_detail)

        # 保存
        if save_to_db:
            rec = {
                "timestamp": datetime.utcnow().isoformat(),
                "num_reviews": len(raw_texts),
                "summary": df_summary.to_dict(orient="records"),
                "details": df_detail.to_dict(orient="records")
            }
            append_record(rec)
            st.success("解析結果を保存しました（data/results.csv）")

        # ダウンロード（JSON）
        buf = io.BytesIO(json.dumps({"summary": cat_rows, "details": detail_rows}, ensure_ascii=False, indent=2).encode("utf-8"))
        st.download_button("解析結果をJSONでダウンロード", data=buf, file_name="review_analysis.json")

# 保存データ表示
if show_saved:
    df_saved = load_records()
    st.subheader("保存済みレコード（最新100件）")
    st.dataframe(df_saved.tail(100))

# review_analysis/sentiment.py
from typing import List, Dict
import re
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# 軽い日本語辞書（ポジティブ/ネガティブ語のサンプル）
JP_POS_WORDS = ["美味しい", "おいしい", "最高", "満足", "おすすめ", "良い", "素晴らしい", "旨い", "うまい"]
JP_NEG_WORDS = ["まずい", "遅い", "不満", "汚い", "残念", "高すぎ", "苦い", "待たされた", "最悪"]

# 文分割の簡易関数
def split_into_sentences(text: str) -> List[str]:
    # 改行または句点で分割（日本語対応の簡易版）
    parts = re.split(r'(?<=[。．！？!?])\s*|\n+', text)
    return [p.strip() for p in parts if p.strip()]

# NLTK準備（VADER）
_nltk_ready = False
def _ensure_nltk():
    global _nltk_ready
    if _nltk_ready:
        return
    try:
        nltk.download("vader_lexicon", quiet=True)
        nltk.download("punkt", quiet=True)
    except Exception:
        pass
    _nltk_ready = True

# 英語文の感情分析（VADER）
def vader_sentiment(text: str) -> Dict:
    _ensure_nltk()
    sia = SentimentIntensityAnalyzer()
    return sia.polarity_scores(text)

# 簡易日本語感情スコア（ルールベース）
def simple_japanese_sentiment(text: str) -> Dict:
    # 0.0 中立 -1..1
    pos = sum(text.count(w) for w in JP_POS_WORDS)
    neg = sum(text.count(w) for w in JP_NEG_WORDS)
    # 単純に正負を算出
    score = pos - neg
    # normalize roughly to -1..1
    if score > 0:
        compound = min(1.0, score / (score + 1))
    elif score < 0:
        compound = max(-1.0, score / (abs(score) + 1))
    else:
        compound = 0.0
    # crude pos/neu/neg distribution
    if compound > 0.05:
        pos_frac, neg_frac, neu_frac = 0.6, 0.0, 0.4
    elif compound < -0.05:
        pos_frac, neg_frac, neu_frac = 0.0, 0.6, 0.4
    else:
        pos_frac, neg_frac, neu_frac = 0.0, 0.0, 1.0

    return {"compound": round(compound, 3), "pos": round(pos_frac,3), "neu": round(neu_frac,3), "neg": round(neg_frac,3)}

# 言語判定（簡易）
def detect_language(text: str) -> str:
    # 英字が多ければen、そうでなければja
    letters = sum(1 for c in text if c.isalpha())
    kana_kanji = sum(1 for c in text if ord(c) > 0x3000)
    if letters > kana_kanji:
        return "en"
    return "ja"

# メイン：複数レビュー（または複数文）を受けて文ごとに解析
def analyze_text_sentences(reviews: List[str]) -> List[Dict]:
    """
    入力: reviews = ["レビュー1", "レビュー2", ...]
    出力: [
      {"text": sentence, "lang": "ja"/"en", "scores": {...}},
      ...
    ]
    """
    rows = []
    for review in reviews:
        sents = split_into_sentences(review)
        for s in sents:
            lang = detect_language(s)
            if lang == "en":
                scores = vader_sentiment(s)
            else:
                scores = simple_japanese_sentiment(s)
            rows.append({"text": s, "lang": lang, "scores": scores})
    return rows

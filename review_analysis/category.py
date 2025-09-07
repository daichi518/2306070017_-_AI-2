# review_analysis/category.py
from typing import List, Dict
from collections import defaultdict
import re

# 分析対象カテゴリ（表示順はここで定義）
TOPICS = ["味", "接客", "雰囲気", "待ち時間", "価格", "清潔感", "その他"]

# 各カテゴリを示すキーワード（代表語）
KEYWORDS = {
    "味": ["味", "おいし", "美味", "まずい", "塩味", "甘い", "辛い", "ソース", "パスタ", "旨い", "うまい"],
    "接客": ["接客", "スタッフ", "店員", "対応", "サービス", "笑顔", "愛想", "態度"],
    "雰囲気": ["雰囲気", "内装", "音楽", "落ち着", "デート", "明るい", "暗い"],
    "待ち時間": ["待ち", "待た", "提供", "行列", "混雑", "時間がかかる"],
    "価格": ["値段", "高い", "安い", "コスパ", "価格", "料金"],
    "清潔感": ["清潔", "汚れ", "掃除", "トイレ", "衛生"],
}

# 文をカテゴリに割当てる（1文が複数カテゴリに該当することもある）
def categorize_sentence(sentence: str) -> List[str]:
    s = sentence.lower()
    assigned = []
    for topic, kws in KEYWORDS.items():
        for kw in kws:
            if kw in s:
                assigned.append(topic)
                break
    if not assigned:
        assigned = ["その他"]
    return assigned

def categorize_sentences_by_topic(sentences_info: List[Dict]) -> Dict[str, List[Dict]]:
    """
    sentences_info: list of {"text": str, "lang": "ja"/"en", "scores": {...}}
    returns dict: topic -> list of sentence dicts (with original info)
    """
    out = defaultdict(list)
    for info in sentences_info:
        text = info["text"]
        cats = categorize_sentence(text)
        for c in cats:
            out[c].append(info)
    # Ensure all topics exist
    for t in TOPICS:
        out.setdefault(t, [])
    return out

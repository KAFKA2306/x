import re
from collections import Counter, defaultdict
from typing import Any
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from src.models import AppConfig, Tweet, TweetAnalysis
def analyze_interests(texts: list[str], config: AppConfig) -> dict[str, Any]:
    txt = " ".join(texts)
    stop = set(config.stop_words)
    kw_words = [w for w in re.findall(r"\b\w{4,}\b", re.sub(r"@\w+", "", txt).lower()) if w not in stop]
    kw = Counter(kw_words)
    ht = Counter(re.findall(r"
    lim = config.limits.top_interests
    return {"top_hashtags": ht.most_common(lim), "top_keywords": kw.most_common(lim), "count": len(texts)}
def analyze_tweets_core(tweets: list[Tweet], config: AppConfig) -> TweetAnalysis:
    df = pd.DataFrame([t.model_dump() for t in tweets])
    txts = [t.full_text for t in tweets]
    v = TfidfVectorizer(max_features=config.limits.tfidf_features, stop_words="english")
    if tweets:
        v_out = v.fit_transform(txts).sum(axis=0).tolist()[0]
        top = sorted(zip(v.get_feature_names_out(), v_out), key=lambda x: x[1], reverse=True)
    else:
        top = []
    return TweetAnalysis(
        total_tweets=len(tweets),
        avg_length=df["char_count"].mean() if not df.empty else 0,
        avg_words=df["word_count"].mean() if not df.empty else 0,
        top_words=top,
        tweets_per_day={str(k): v for k, v in df.groupby(df["created_at"].dt.date).size().items()},
        tweets_per_week={str(k): int(v) for k, v in df.groupby(df["created_at"].dt.to_period("M")).size().items()},
        tweets_per_hour=df.groupby(df["created_at"].dt.hour).size().to_dict(),
        tweets_by_type={
            "original": df["is_original"].sum(),
            "retweet": df["is_retweet"].sum(),
            "reply": df["is_reply"].sum(),
        },
        word_freq=dict(Counter(" ".join(txts).split()).most_common(config.limits.word_freq)),
    )
def analyze_graph_core(followers: list[str], following: list[str]) -> dict[str, Any]:
    fer, fing = set(followers), set(following)
    mut, fans, non = fing & fer, fer - fing, fing - fer
    l_fer, l_fing = len(fer), len(fing)
    return {
        "stats": {
            "total_followers": l_fer,
            "total_following": l_fing,
            "non_followers_count": len(non),
            "fans_count": len(fans),
            "mutuals_count": len(mut),
            "follow_back_rate": round(len(mut) / l_fing * 100, 1) if l_fing else 0,
            "fan_ratio": round(len(fans) / l_fer * 100, 1) if l_fer else 0,
            "ff_ratio": round(l_fer / l_fing, 2) if l_fing else 0,
        },
        "non_followers_sample": list(non)[:10],
        "fans_sample": list(fans)[:10],
    }
def analyze_efficiency_core(tweets: list[Tweet]) -> dict[str, dict[int, float]]:
    slots = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for t in tweets:
        e = t.favorite_count + t.retweet_count
        d, h = days[t.created_at.weekday()], t.created_at.hour
        slots[d][h][0] += e
        slots[d][h][1] += 1
    return {
        d: {h: round(slots[d][h][0] / slots[d][h][1], 2) if slots[d][h][1] > 0 else 0.0 for h in range(24)}
        for d in days
    }

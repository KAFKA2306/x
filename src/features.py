from typing import Counter, List

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.models import AppConfig, Tweet, TweetAnalysis


def analyze_tweets(tweets: List[Tweet], config: AppConfig) -> TweetAnalysis:
    df = pd.DataFrame([t.model_dump() for t in tweets])

    total_tweets = len(tweets)
    avg_length = df["char_count"].mean() if not df.empty else 0
    avg_words = df["word_count"].mean() if not df.empty else 0

    all_text = " ".join([t.full_text for t in tweets])
    words = [w for w in all_text.split() if len(w) > 1]
    word_freq = Counter(words)

    vectorizer = TfidfVectorizer(max_features=config.limits.tfidf_features, stop_words="english")

    if tweets:
        tfidf_matrix = vectorizer.fit_transform([t.full_text for t in tweets])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.sum(axis=0).tolist()[0]
        top_words = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
    else:
        top_words = []

    tweets_per_day = df.groupby(df["created_at"].dt.date).size().to_dict()
    tweets_per_day_str = {str(k): v for k, v in tweets_per_day.items()}

    tweets_per_week = df.groupby(df["created_at"].dt.to_period("M")).size().to_dict()
    tweets_per_week_str = {str(k): int(v) for k, v in tweets_per_week.items()}

    tweets_per_hour = df.groupby(df["created_at"].dt.hour).size().to_dict()

    tweets_by_type = {
        "original": df["is_original"].sum(),
        "retweet": df["is_retweet"].sum(),
        "reply": df["is_reply"].sum(),
    }

    return TweetAnalysis(
        total_tweets=total_tweets,
        avg_length=avg_length,
        avg_words=avg_words,
        top_words=top_words,
        tweets_per_day=tweets_per_day_str,
        tweets_per_week=tweets_per_week_str,
        tweets_per_hour=tweets_per_hour,
        tweets_by_type=tweets_by_type,
        word_freq=dict(word_freq.most_common(config.limits.word_freq)),
    )

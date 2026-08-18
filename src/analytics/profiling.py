from collections import Counter
from dataclasses import dataclass

from src.models import AppConfig, Tweet


@dataclass
class UserProfile:
    total_tweets: int
    tweets_per_day: float
    peak_hour: int
    content_mix: dict[str, float]
    avg_engagement: float
    avg_chars: float
    avg_words: float
    mention_rate: float
    reply_rate: float
    top_keywords: list[tuple[str, int]]
    top_hashtags: list[tuple[str, int]]
    best_tweets: list[dict]
    monthly_trend: dict[str, int]


def analyze_profile(tweets: list[Tweet], config: AppConfig) -> UserProfile:
    if not tweets:
        return UserProfile(
            total_tweets=0,
            tweets_per_day=0,
            peak_hour=0,
            content_mix={},
            avg_engagement=0,
            avg_chars=0,
            avg_words=0,
            mention_rate=0,
            reply_rate=0,
            top_keywords=[],
            top_hashtags=[],
            best_tweets=[],
            monthly_trend={},
        )

    n = len(tweets)
    dates = sorted(t.created_at.date() for t in tweets)
    days_span = max((dates[-1] - dates[0]).days, 1)

    hours = Counter(t.created_at.hour for t in tweets)
    peak_hour = hours.most_common(1)[0][0] if hours else 0

    orig = sum(1 for t in tweets if t.is_original)
    rt = sum(1 for t in tweets if t.is_retweet)
    rp = sum(1 for t in tweets if t.is_reply)

    content_mix = {
        "original": round(orig / n * 100, 1),
        "retweet": round(rt / n * 100, 1),
        "reply": round(rp / n * 100, 1),
    }

    total_eng = sum(t.favorite_count + t.retweet_count for t in tweets)
    avg_eng = round(total_eng / n, 2)

    avg_chars = round(sum(t.char_count for t in tweets) / n, 1)
    avg_words = round(sum(t.word_count for t in tweets) / n, 1)

    mentions = sum(t.mention_count for t in tweets)
    mention_rate = round(mentions / n, 2)
    reply_rate = round(rp / n * 100, 1)

    all_words = []
    all_hashtags = []
    stop = set(config.stop_words)
    for t in tweets:
        if not t.is_retweet:
            words = [
                w.lower() for w in t.full_text.split() if len(w) > 3 and w.lower() not in stop and not w.startswith("@")
            ]
            all_words.extend(words)
            all_hashtags.extend(t.hashtags)

    lim = config.limits.top_interests
    top_keywords = Counter(all_words).most_common(lim)
    top_hashtags = Counter(all_hashtags).most_common(lim)

    sorted_by_eng = sorted(tweets, key=lambda t: t.favorite_count + t.retweet_count, reverse=True)
    best = sorted_by_eng[:5]
    best_tweets = [
        {
            "text": t.full_text[:100],
            "likes": t.favorite_count,
            "rts": t.retweet_count,
            "date": t.created_at.strftime("%Y-%m-%d"),
        }
        for t in best
    ]

    monthly = Counter(t.created_at.strftime("%Y-%m") for t in tweets)
    monthly_trend = dict(sorted(monthly.items()))

    return UserProfile(
        total_tweets=n,
        tweets_per_day=round(n / days_span, 2),
        peak_hour=peak_hour,
        content_mix=content_mix,
        avg_engagement=avg_eng,
        avg_chars=avg_chars,
        avg_words=avg_words,
        mention_rate=mention_rate,
        reply_rate=reply_rate,
        top_keywords=top_keywords,
        top_hashtags=top_hashtags,
        best_tweets=best_tweets,
        monthly_trend=monthly_trend,
    )

from src.models import Tweet

FOCUS_METRICS: dict[str, list[str]] = {
    "default": ["tweets_per_day", "top_words", "tweets_by_type"],
    "vrchat": ["media_tweets", "top_replied", "photo_frequency"],
}


def get_focus_metrics(preset: str) -> list[str]:
    return FOCUS_METRICS.get(preset, FOCUS_METRICS["default"])


def match_keywords(tweet: Tweet, keywords: list[str]) -> bool:
    return any(kw in tweet.full_text.lower() for kw in keywords)

import re
from collections import Counter
from typing import Dict, List

from src.models import AppConfig, Like, Tweet


def extract_interests(texts: List[str], stop_words: List[str], limit: int) -> Dict[str, any]:
    all_text = " ".join(texts)

    hashtags = re.findall(r"#(\w+)", all_text)
    hashtag_counts = Counter(hashtags)

    text_no_mentions = re.sub(r"@\w+", "", all_text)
    words = re.findall(r"\b\w{4,}\b", text_no_mentions.lower())
    filtered_words = [w for w in words if w not in set(stop_words)]
    word_counts = Counter(filtered_words)

    return {
        "top_hashtags": hashtag_counts.most_common(limit),
        "top_keywords": word_counts.most_common(limit),
        "total_count": len(texts),
    }


def analyze_likes_interests(likes: List[Like], config: AppConfig) -> Dict[str, any]:
    texts = [like.full_text for like in likes]
    result = extract_interests(texts, config.stop_words, config.limits.top_interests)
    result["total_likes"] = result.pop("total_count")
    return result


def analyze_tweets_interests(tweets: List[Tweet], config: AppConfig) -> Dict[str, any]:
    original = [t.full_text for t in tweets if t.is_original]
    retweets = [t.full_text for t in tweets if t.is_retweet]
    replies = [t.full_text for t in tweets if t.is_reply]

    args = (config.stop_words, config.limits.top_interests)

    return {
        "original": {**extract_interests(original, *args), "label": "Original", "count": len(original)},
        "retweets": {**extract_interests(retweets, *args), "label": "Retweets", "count": len(retweets)},
        "replies": {**extract_interests(replies, *args), "label": "Replies", "count": len(replies)},
    }

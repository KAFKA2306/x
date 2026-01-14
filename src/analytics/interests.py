import re
from collections import Counter
from typing import Dict, List

from src.models import Like, Tweet

STOP_WORDS = {
    "the", "and", "for", "that", "this", "with", "from", "have", "http", "https", "com", "www",
    "you", "your", "they", "them", "their", "there", "here", "what", "who", "which", "when", "where", "why", "how",
    "are", "was", "were", "been", "being", "will", "would", "could", "should", "can", "may", "might", "must",
    "have", "has", "had", "does", "did", "doing", "done", "just", "only", "also", "very", "really", "more", "most",
    "some", "any", "all", "each", "every", "both", "other", "another", "such", "same", "than", "then", "too",
    "about", "after", "before", "into", "over", "under", "again", "because", "while", "during", "through",
    "like", "want", "need", "know", "think", "make", "take", "come", "give", "look", "going", "still",
    "view", "post", "posts", "account", "accounts", "learnmore", "learn", "more",
    "suspended", "suspend", "limits", "limit", "limited", "unable", "owner", "owners",
    "amp", "content", "twitter", "tweet", "tweets", "retweet", "retweets",
    "follow", "following", "followers", "unfollow",
    "likes", "liked", "reply", "replies", "quote", "quoted",
    "media", "photo", "photos", "video", "videos", "image", "images",
    "link", "links", "click", "share", "shared", "see", "read",
    "new", "now", "today", "time", "day", "days", "week", "weeks", "year", "years",
    "get", "got", "thing", "things", "something", "people", "person", "really", "actually",
    "おはようございます", "こんにちは", "こんばんは", "ありがとう", "ありがとうございます",
    "よろしくお願いします", "お疲れ様です", "で購入しました", "購入しました",
    "これは", "それは", "あれは", "ですね", "ですが", "します", "しました",
    "ください", "いただき", "について", "ことが", "という", "として", "における",
}


def extract_interests(texts: List[str]) -> Dict[str, any]:
    all_text = " ".join(texts)

    hashtags = re.findall(r"#(\w+)", all_text)
    hashtag_counts = Counter(hashtags)

    words = re.findall(r"\b\w{4,}\b", all_text.lower())
    filtered_words = [w for w in words if w not in STOP_WORDS]
    word_counts = Counter(filtered_words)

    return {
        "top_hashtags": hashtag_counts.most_common(20),
        "top_keywords": word_counts.most_common(20),
        "total_count": len(texts),
    }


def analyze_likes_interests(likes: List[Like]) -> Dict[str, any]:
    texts = [like.full_text for like in likes]
    result = extract_interests(texts)
    result["total_likes"] = result.pop("total_count")
    return result


def analyze_tweets_interests(tweets: List[Tweet]) -> Dict[str, any]:
    original = [t.full_text for t in tweets if t.is_original]
    retweets = [t.full_text for t in tweets if t.is_retweet]
    replies = [t.full_text for t in tweets if t.is_reply]

    return {
        "original": {**extract_interests(original), "label": "Original", "count": len(original)},
        "retweets": {**extract_interests(retweets), "label": "Retweets", "count": len(retweets)},
        "replies": {**extract_interests(replies), "label": "Replies", "count": len(replies)},
    }

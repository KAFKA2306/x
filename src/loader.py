import json
import re
from datetime import datetime

from src.adapters import parse_archive
from src.models import Tweet


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"http\S+", "", text)
    return text


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%a %b %d %H:%M:%S +0000 %Y")


def load_tweets(file_path: str) -> list[Tweet]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    raw_tweets = parse_archive(content)
    tweets = []

    for item in raw_tweets:
        if "full_text" not in item["tweet"]:
            continue

        tweet_data = item["tweet"]
        full_text = clean_text(tweet_data["full_text"])
        created_at = parse_date(tweet_data["created_at"])

        is_retweet = full_text.startswith("RT @")
        is_reply = full_text.startswith("@")
        is_original = not (is_retweet or is_reply)

        retweeted_user = None
        reply_to_user = None
        if is_retweet:
            match = re.search(r"RT @(\w+)", full_text)
            if match:
                retweeted_user = match.group(1)
        elif is_reply:
            match = re.search(r"^@(\w+)", full_text)
            if match:
                reply_to_user = match.group(1)

        tweet = Tweet(
            created_at=created_at,
            full_text=full_text,
            is_retweet=is_retweet,
            is_reply=is_reply,
            is_original=is_original,
            char_count=len(full_text),
            word_count=len(full_text.split()),
            mention_count=full_text.count("@"),
            hashtag_count=full_text.count("#"),
            url_count=tweet_data["full_text"].count("http"),
            favorite_count=int(tweet_data.get("favorite_count", 0)),
            retweet_count=int(tweet_data.get("retweet_count", 0)),
            reply_to_user=reply_to_user,
            retweeted_user=retweeted_user,
        )
        tweets.append(tweet)

    return tweets


def load_user_list(input_file: str) -> list[str]:
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    data = parse_archive(content)
    user_ids = []
    for item in data:
        if "follower" in item:
            user_ids.append(item["follower"].get("accountId", "unknown"))
        elif "following" in item:
            user_ids.append(item["following"].get("accountId", "unknown"))
    return user_ids

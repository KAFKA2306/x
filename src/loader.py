import json
import re
from datetime import datetime
from typing import Any

from src.models import Like, Tweet


def parse_archive(content: str) -> list[dict[str, Any]]:
    cleaned = re.sub(r"window\.YTD\.\w+\.part0\s*=\s*", "", content)
    return json.loads(cleaned)


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
        tweet_data = item["tweet"]
        full_text = clean_text(tweet_data["full_text"])
        created_at = parse_date(tweet_data["created_at"])

        entities = tweet_data.get("entities", {})
        extended_entities = tweet_data.get("extended_entities", {})

        hashtags = [h["text"] for h in entities.get("hashtags", [])]
        user_mentions = entities.get("user_mentions", [])
        mentions = [m["screen_name"] for m in user_mentions]
        mention_user_ids = [m.get("id_str", "") for m in user_mentions if m.get("id_str")]

        media_list = extended_entities.get("media", [])
        media_count = len(media_list)
        has_media = media_count > 0

        is_retweet = full_text.startswith("RT @")
        is_reply = full_text.startswith("@")
        is_original = not (is_retweet or is_reply)

        reply_to_user = tweet_data.get("in_reply_to_screen_name")
        reply_to_user_id = tweet_data.get("in_reply_to_user_id_str")

        retweeted_user = None
        retweeted_user_id = None
        if is_retweet:
            match = re.search(r"RT @(\w+)", full_text)
            if match:
                retweeted_user = match.group(1)
            if user_mentions:
                retweeted_user_id = user_mentions[0].get("id_str")

        tweets.append(
            Tweet(
                created_at=created_at,
                full_text=full_text,
                is_retweet=is_retweet,
                is_reply=is_reply,
                is_original=is_original,
                char_count=len(full_text),
                word_count=len(full_text.split()),
                mention_count=len(mentions),
                hashtag_count=len(hashtags),
                url_count=len(entities.get("urls", [])),
                favorite_count=int(tweet_data.get("favorite_count", 0)),
                retweet_count=int(tweet_data.get("retweet_count", 0)),
                reply_to_user=reply_to_user,
                retweeted_user=retweeted_user,
                media_count=media_count,
                has_media=has_media,
                hashtags=hashtags,
                mentions=mentions,
                mention_user_ids=mention_user_ids,
                reply_to_user_id=reply_to_user_id,
                retweeted_user_id=retweeted_user_id,
            )
        )

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


def load_likes(file_path: str) -> list[Like]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    data = parse_archive(content)
    likes = []

    for item in data:
        like_data = item["like"]
        likes.append(
            Like(
                tweet_id=like_data.get("tweetId", ""),
                full_text=clean_text(like_data.get("fullText", "")),
                expanded_url=like_data.get("expandedUrl", ""),
                mentions=re.findall(r"@(\w+)", like_data.get("fullText", "")),
            )
        )

    return likes


def extract_user_map(file_path: str) -> dict[str, str]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    raw_tweets = parse_archive(content)
    user_map = {}

    for item in raw_tweets:
        tweet_data = item.get("tweet", {})
        entities = tweet_data.get("entities", {})
        user_mentions = entities.get("user_mentions", [])

        for m in user_mentions:
            if "id_str" in m and "screen_name" in m:
                user_map[m["id_str"]] = m["screen_name"]

        if "in_reply_to_user_id_str" in tweet_data and "in_reply_to_screen_name" in tweet_data:
            user_map[tweet_data["in_reply_to_user_id_str"]] = tweet_data["in_reply_to_screen_name"]

    return user_map

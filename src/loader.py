import json
import re
from datetime import datetime
from typing import Any
from src.models import Like, Tweet
def parse_archive(content: str) -> list[dict[str, Any]]:
    return json.loads(re.sub(r"window\.YTD\.\w+\.part0\s*=\s*", "", content))
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"http\S+", "", text)
def load_tweets(path: str) -> list[Tweet]:
    with open(path, "r", encoding="utf-8") as f:
        data = parse_archive(f.read())
    res = []
    for item in data:
        if "tweet" not in item:
            continue
        t = item["tweet"]
        txt = clean_text(t.get("full_text", ""))
        ent = t.get("entities", {})
        mentions = ent.get("user_mentions", [])
        rt = txt.startswith("RT @")
        res.append(
            Tweet(
                created_at=datetime.strptime(t.get("created_at", ""), "%a %b %d %H:%M:%S +0000 %Y"),
                full_text=txt,
                is_retweet=rt,
                is_reply=txt.startswith("@"),
                is_original=not (rt or txt.startswith("@")),
                char_count=len(txt),
                word_count=len(txt.split()),
                mention_count=len(mentions),
                hashtag_count=len(ent.get("hashtags", [])),
                url_count=len(ent.get("urls", [])),
                favorite_count=int(t.get("favorite_count", 0)),
                retweet_count=int(t.get("retweet_count", 0)),
                reply_to_user=t.get("in_reply_to_screen_name"),
                retweeted_user=mentions[0].get("screen_name") if rt and mentions else None,
                hashtags=[h["text"] for h in ent.get("hashtags", [])],
                mentions=[m["screen_name"] for m in mentions],
                urls=[u.get("expanded_url", "") for u in ent.get("urls", [])],
                mention_user_ids=[m.get("id_str", "") for m in mentions],
                reply_to_user_id=t.get("in_reply_to_user_id_str"),
                retweeted_user_id=mentions[0].get("id_str") if rt and mentions else None,
            )
        )
    return res
def load_user_list(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        data = parse_archive(f.read())
    return [i.get("follower", i.get("following", {})).get("accountId", "unknown") for i in data]
def load_likes(path: str) -> list[Like]:
    with open(path, "r", encoding="utf-8") as f:
        data = parse_archive(f.read())
    return [
        Like(
            tweet_id=i["like"].get("tweetId", ""),
            full_text=clean_text(i["like"].get("fullText", "")),
            expanded_url=i["like"].get("expandedUrl", ""),
            mentions=re.findall(r"@(\w+)", i["like"].get("fullText", "")),
        )
        for i in data
        if "like" in i
    ]
def load_mutes(path: str) -> set[str]:
    with open(path, "r", encoding="utf-8") as f:
        data = parse_archive(f.read())
    return {i["muting"].get("accountId", "") for i in data if "muting" in i}

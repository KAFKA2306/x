import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from src.models import AppConfig, Like, Tweet


class ArchiveInputStatus(str, Enum):
    READY = "ready"
    VALID_EMPTY = "valid_empty"
    OPTIONAL_MISSING = "optional_missing"
    MISSING_REQUIRED = "missing_required"
    INVALID = "invalid"


@dataclass(frozen=True)
class ArchiveInputReadiness:
    name: str
    path: str
    required: bool
    status: ArchiveInputStatus
    error: str | None = None


@dataclass(frozen=True)
class ArchiveInputs:
    tweets: list[Tweet]
    follower: list[str]
    following: list[str]
    like: list[Like]
    mute: set[str]
    readiness: dict[str, ArchiveInputReadiness]

    @property
    def analysis_ready(self) -> bool:
        return all(
            item.status not in {ArchiveInputStatus.MISSING_REQUIRED, ArchiveInputStatus.INVALID}
            for item in self.readiness.values()
        )


def parse_archive(content: str) -> list[dict[str, Any]]:
    parsed = json.loads(re.sub(r"window\.YTD\.\w+\.part0\s*=\s*", "", content))
    if not isinstance(parsed, list):
        raise ValueError("archive payload must be a JSON array")
    if not all(isinstance(item, dict) for item in parsed):
        raise ValueError("archive entries must be JSON objects")
    return parsed


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


def load_archive_inputs(config: AppConfig) -> ArchiveInputs:
    loaders: dict[str, tuple[Callable[[str], Any], Any]] = {
        "tweets": (load_tweets, []),
        "follower": (load_user_list, []),
        "following": (load_user_list, []),
        "like": (load_likes, []),
        "mute": (load_mutes, set()),
    }
    required = set(config.archive_inputs.required)
    optional = set(config.archive_inputs.optional)
    known = set(loaders)
    if required & optional:
        raise ValueError("archive input cannot be both required and optional")
    configured = required | optional
    if configured != known:
        missing = sorted(known - configured)
        unknown = sorted(configured - known)
        raise ValueError(f"archive input policy mismatch: missing={missing}, unknown={unknown}")

    values: dict[str, Any] = {}
    readiness: dict[str, ArchiveInputReadiness] = {}
    for name, (loader, empty_value) in loaders.items():
        path = getattr(config.files, name)
        is_required = name in required
        if not Path(path).is_file():
            status = ArchiveInputStatus.MISSING_REQUIRED if is_required else ArchiveInputStatus.OPTIONAL_MISSING
            values[name] = empty_value
            readiness[name] = ArchiveInputReadiness(name, path, is_required, status)
            continue
        try:
            value = loader(path)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            values[name] = empty_value
            readiness[name] = ArchiveInputReadiness(name, path, is_required, ArchiveInputStatus.INVALID, str(exc))
            continue
        values[name] = value
        status = ArchiveInputStatus.READY if value else ArchiveInputStatus.VALID_EMPTY
        readiness[name] = ArchiveInputReadiness(name, path, is_required, status)

    return ArchiveInputs(
        tweets=values["tweets"],
        follower=values["follower"],
        following=values["following"],
        like=values["like"],
        mute=values["mute"],
        readiness=readiness,
    )

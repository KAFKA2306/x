import csv
import io

from src.models import AccountScore, Tweet


def export_account_scores_to_csv(scores: list[AccountScore]) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    fields = [
        "account_id",
        "screen_name",
        "score",
        "follows_back",
        "reply_count",
        "retweet_count",
        "mention_count",
        "like_count",
        "user_link",
        "category",
    ]
    w.writerow(fields)
    for s in scores:
        w.writerow([getattr(s, f) for f in fields])
    return out.getvalue()


def export_tweets_to_csv(tweets: list[Tweet]) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["created_at", "full_text", "type", "favorite_count", "retweet_count", "reply_to", "retweeted_user"])
    for t in tweets:
        tp = "retweet" if t.is_retweet else "reply" if t.is_reply else "original"
        w.writerow(
            [
                t.created_at.isoformat(),
                t.full_text,
                tp,
                t.favorite_count,
                t.retweet_count,
                t.reply_to_user or "",
                t.retweeted_user or "",
            ]
        )
    return out.getvalue()

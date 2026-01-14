import csv
import io

from src.models import AccountScore, Tweet


def export_account_scores_to_csv(scores: list[AccountScore]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "account_id",
            "screen_name",
            "score",
            "follows_back",
            "reply_count",
            "retweet_count",
            "mention_count",
            "like_count",
            "user_link",
        ]
    )

    for s in scores:
        writer.writerow(
            [
                s.account_id,
                s.screen_name,
                s.score,
                s.follows_back,
                s.reply_count,
                s.retweet_count,
                s.mention_count,
                s.like_count,
                s.user_link,
            ]
        )

    return output.getvalue()


def export_tweets_to_csv(tweets: list[Tweet]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "created_at",
            "full_text",
            "type",
            "favorite_count",
            "retweet_count",
            "reply_to",
            "retweeted_user",
        ]
    )

    for t in tweets:
        tweet_type = "original"
        if t.is_retweet:
            tweet_type = "retweet"
        elif t.is_reply:
            tweet_type = "reply"

        writer.writerow(
            [
                t.created_at.isoformat(),
                t.full_text,
                tweet_type,
                t.favorite_count,
                t.retweet_count,
                t.reply_to_user or "",
                t.retweeted_user or "",
            ]
        )

    return output.getvalue()

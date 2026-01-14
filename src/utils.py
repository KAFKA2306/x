from datetime import datetime, timezone


def snowflake_to_datetime(tweet_id: str | int) -> datetime:
    """
    Convert a Twitter Snowflake ID to a datetime object.
    Twitter Snowflake ID format: (timestamp - 1288834974657) << 22
    """
    tweet_id_int = int(tweet_id)
    timestamp = (tweet_id_int >> 22) + 1288834974657
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)

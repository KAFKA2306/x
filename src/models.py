from datetime import datetime

from pydantic import BaseModel


class Tweet(BaseModel):
    created_at: datetime
    full_text: str
    is_retweet: bool = False
    is_reply: bool = False
    is_original: bool = True
    char_count: int = 0
    word_count: int = 0
    mention_count: int = 0
    hashtag_count: int = 0
    url_count: int = 0
    favorite_count: int = 0
    retweet_count: int = 0
    reply_to_user: str | None = None
    retweeted_user: str | None = None
    media_count: int = 0
    has_media: bool = False


class InteractionStats(BaseModel):
    top_replied: list[tuple[str, int]]
    top_retweeted: list[tuple[str, int]]
    total_replies: int
    total_retweets: int


class TweetAnalysis(BaseModel):
    total_tweets: int
    avg_length: float
    avg_words: float
    top_words: list[tuple[str, float]]
    tweets_per_day: dict[str, int]
    tweets_per_hour: dict[int, int]
    tweets_by_type: dict[str, int]
    word_freq: dict[str, int]


class AppConfig(BaseModel):
    input_file: str
    output_dir: str
    model_name: str
    preset: str = "default"
    vrchat_keywords: list[str] = []
    photo_keywords: list[str] = []

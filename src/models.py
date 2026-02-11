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
    hashtags: list[str] = []
    mentions: list[str] = []
    urls: list[str] = []
    mention_user_ids: list[str] = []
    reply_to_user_id: str | None = None
    retweeted_user_id: str | None = None
class InteractionStats(BaseModel):
    top_replied: list[tuple[str, int]]
    top_retweeted: list[tuple[str, int]]
    top_hashtags: list[tuple[str, int]]
    top_mentions: list[tuple[str, int]]
    total_replies: int
    total_retweets: int
class TweetAnalysis(BaseModel):
    total_tweets: int
    avg_length: float
    avg_words: float
    top_words: list[tuple[str, float]]
    tweets_per_day: dict[str, int]
    tweets_per_week: dict[str, int]
    tweets_per_hour: dict[int, int]
    tweets_by_type: dict[str, int]
    word_freq: dict[str, int]
class ScoringWeights(BaseModel):
    follower: int = 10
    reply: int = 3
    retweet: int = 1
    mention: int = 2
    like: int = 2
    quote: int = 4
class AnalyticsLimits(BaseModel):
    tfidf_features: int = 20
    word_freq: int = 100
    top_stats: int = 10
    top_interests: int = 20
    mutuals: int = 20
class FileConfig(BaseModel):
    tweets: str = "data/tweets.js"
    follower: str = "data/follower.js"
    following: str = "data/following.js"
    like: str = "data/like.js"
    mute: str = "data/mute.js"
class AppConfig(BaseModel):
    input_file: str
    output_dir: str
    model_name: str
    preset: str = "default"
    files: FileConfig = FileConfig()
    vrchat_keywords: list[str] = []
    photo_keywords: list[str] = []
    stop_words: list[str] = []
    weights: ScoringWeights = ScoringWeights()
    limits: AnalyticsLimits = AnalyticsLimits()
class Like(BaseModel):
    tweet_id: str
    full_text: str
    expanded_url: str
    mentions: list[str] = []
class AccountScore(BaseModel):
    account_id: str
    screen_name: str
    user_link: str
    score: int
    follows_back: bool
    reply_count: int
    retweet_count: int
    mention_count: int
    like_count: int
    quote_count: int = 0
    category: str = ""
    is_muted: bool = False

from collections import Counter

from src.models import InteractionStats, Tweet


class AudienceAnalytics:
    def __init__(self, tweets: list[Tweet]):
        self.tweets = tweets

    def analyze_interactions(self) -> InteractionStats:
        replies: Counter[str] = Counter()
        retweets: Counter[str] = Counter()

        for t in self.tweets:
            if t.retweeted_user:
                retweets[t.retweeted_user] += 1
            elif t.reply_to_user:
                replies[t.reply_to_user] += 1

        return InteractionStats(
            top_replied=replies.most_common(10),
            top_retweeted=retweets.most_common(10),
            total_replies=sum(replies.values()),
            total_retweets=sum(retweets.values()),
        )

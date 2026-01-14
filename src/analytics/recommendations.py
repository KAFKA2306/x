from collections import Counter

from src.models import AccountScore, AppConfig, Like, Tweet


def build_account_map(tweets: list[Tweet]) -> dict[str, str]:
    account_map = {}
    for t in tweets:
        if t.reply_to_user_id and t.reply_to_user:
            account_map[t.reply_to_user_id] = t.reply_to_user

        if t.retweeted_user_id and t.retweeted_user:
            account_map[t.retweeted_user_id] = t.retweeted_user

    return account_map


def extract_interaction_counts(
    tweets: list[Tweet], likes: list[Like], account_map: dict[str, str]
) -> tuple[Counter[str], Counter[str], Counter[str], Counter[str]]:
    reply_counts: Counter[str] = Counter()
    retweet_counts: Counter[str] = Counter()
    mention_counts: Counter[str] = Counter()
    like_counts: Counter[str] = Counter()

    for t in tweets:
        if t.reply_to_user_id:
            reply_counts[t.reply_to_user_id] += 1
            if t.reply_to_user:
                account_map[t.reply_to_user_id] = t.reply_to_user

        if t.retweeted_user_id:
            retweet_counts[t.retweeted_user_id] += 1
            if t.retweeted_user:
                account_map[t.retweeted_user_id] = t.retweeted_user

        for uid in t.mention_user_ids:
            mention_counts[uid] += 1

    screen_name_to_id = {v: k for k, v in account_map.items()}

    for like in likes:
        for screen_name in like.mentions:
            if screen_name in screen_name_to_id:
                uid = screen_name_to_id[screen_name]
                like_counts[uid] += 1

    return reply_counts, retweet_counts, mention_counts, like_counts


class RecommendationAnalytics:
    def __init__(
        self,
        config: AppConfig,
        followers: set[str],
        following: set[str],
        reply_counts: Counter[str],
        retweet_counts: Counter[str],
        mention_counts: Counter[str],
        like_counts: Counter[str],
        account_map: dict[str, str],
    ):
        self.config = config
        self.followers = followers
        self.following = following
        self.reply_counts = reply_counts
        self.retweet_counts = retweet_counts
        self.mention_counts = mention_counts
        self.like_counts = like_counts
        self.account_map = account_map

    def score_account(self, account_id: str) -> int:
        score = 0
        weights = self.config.weights

        if account_id in self.followers:
            score += weights.follower

        score += self.reply_counts.get(account_id, 0) * weights.reply
        score += self.retweet_counts.get(account_id, 0) * weights.retweet
        score += self.mention_counts.get(account_id, 0) * weights.mention
        score += self.like_counts.get(account_id, 0) * weights.like

        return score

    def _create_account_score(self, account_id: str) -> AccountScore:
        score = self.score_account(account_id)
        screen_name = self.account_map.get(account_id, "unknown")

        if screen_name != "unknown":
            user_link = f"https://twitter.com/{screen_name}"
        else:
            user_link = f"https://twitter.com/i/user/{account_id}"

        return AccountScore(
            account_id=account_id,
            screen_name=screen_name,
            user_link=user_link,
            score=score,
            follows_back=account_id in self.followers,
            reply_count=self.reply_counts.get(account_id, 0),
            retweet_count=self.retweet_counts.get(account_id, 0),
            mention_count=self.mention_counts.get(account_id, 0),
            like_count=self.like_counts.get(account_id, 0),
        )

    def get_unfollow_candidates(self, limit: int | None = None) -> list[AccountScore]:
        non_followers = self.following - self.followers

        candidates = []
        for account_id in non_followers:
            score = self.score_account(account_id)
            if score == 0:
                candidates.append(self._create_account_score(account_id))

        candidates.sort(key=lambda x: x.account_id)

        if limit is not None and limit > 0:
            return candidates[:limit]
        return candidates

    def get_valuable_mutuals(self, limit: int | None = None) -> list[AccountScore]:
        mutuals = self.following & self.followers

        valuable = []
        for account_id in mutuals:
            valuable.append(self._create_account_score(account_id))

        valuable.sort(key=lambda x: x.score, reverse=True)

        if limit is None:
            limit = self.config.limits.mutuals

        if limit > 0:
            return valuable[:limit]
        return valuable

    def get_all_interactions(self, limit: int | None = None) -> list[AccountScore]:
        all_ids = set()
        all_ids.update(self.reply_counts.keys())
        all_ids.update(self.retweet_counts.keys())
        all_ids.update(self.mention_counts.keys())
        all_ids.update(self.like_counts.keys())
        all_ids.update(self.followers)
        all_ids.update(self.following)

        scores = []
        for account_id in all_ids:
            scores.append(self._create_account_score(account_id))

        scores.sort(key=lambda x: x.score, reverse=True)

        if limit is not None and limit > 0:
            return scores[:limit]
        return scores

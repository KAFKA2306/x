import re
from collections import Counter
from src.models import AccountScore, AppConfig, Like, Tweet
def extract_interactions(
    tweets: list[Tweet], likes: list[Like], account_map: dict[str, str], config: AppConfig
) -> tuple[dict[str, Counter], Counter]:
    ids = {k: Counter() for k in ["reply", "retweet", "mention", "like", "quote"]}
    hashtags = Counter()
    quote_pattern = re.compile(r"(?:twitter|x)\.com/(\w+)/status/\d+")
    for t in reversed(tweets):
        if t.reply_to_user_id:
            ids["reply"][t.reply_to_user_id] += 1
            account_map[t.reply_to_user_id] = t.reply_to_user or account_map.get(t.reply_to_user_id, "")
        if t.retweeted_user_id:
            ids["retweet"][t.retweeted_user_id] += 1
            account_map[t.retweeted_user_id] = t.retweeted_user or account_map.get(t.retweeted_user_id, "")
        for uid, sn in zip(t.mention_user_ids, t.mentions):
            ids["mention"][uid] += 1
            account_map[uid] = sn or account_map.get(uid, "")
        for h in t.hashtags:
            hashtags[h] += 1
        for url in t.urls:
            m = quote_pattern.search(url)
            if m:
                quoted_sn = m.group(1).lower()
                if quoted_sn not in ("i", "intent"):
                    sn_to_id = {v.lower(): k for k, v in account_map.items()}
                    if quoted_sn in sn_to_id:
                        ids["quote"][sn_to_id[quoted_sn]] += 1
    s_to_id = {v: k for k, v in account_map.items()}
    for lt in likes:
        for s in lt.mentions:
            if s in s_to_id:
                ids["like"][s_to_id[s]] += 1
    return ids, hashtags
class RecommendationAnalytics:
    def __init__(
        self,
        config: AppConfig,
        followers: set[str],
        following: set[str],
        counts: dict[str, Counter],
        account_map: dict[str, str],
        muted: set[str] | None = None,
    ):
        self.config = config
        self.followers = followers
        self.following = following
        self.counts = counts
        self.account_map = account_map
        self.muted = muted or set()
    def score(self, aid: str) -> int:
        w = self.config.weights
        s = w.follower if aid in self.followers else 0
        keys = ["reply", "retweet", "mention", "like", "quote"]
        return s + sum(self.counts[k].get(aid, 0) * getattr(w, k) for k in keys)
    def _create(self, aid: str) -> AccountScore:
        s = self.score(aid)
        sn = self.account_map.get(aid, "unknown")
        is_fer, is_fing = aid in self.followers, aid in self.following
        if is_fer and is_fing:
            cat = "Mutual" if s > 0 else "Ghost"
        elif is_fer:
            cat = "Fan"
        elif is_fing:
            cat = "Unfollow Candidate" if s == 0 else "Unrequited"
        else:
            cat = "Other"
        link = f"https://x.com/{sn}" if sn != "unknown" else f"https://x.com/i/user/{aid}"
        return AccountScore(
            account_id=aid,
            screen_name=sn,
            user_link=link,
            score=s,
            follows_back=is_fer,
            reply_count=self.counts["reply"].get(aid, 0),
            retweet_count=self.counts["retweet"].get(aid, 0),
            mention_count=self.counts["mention"].get(aid, 0),
            like_count=self.counts["like"].get(aid, 0),
            quote_count=self.counts["quote"].get(aid, 0),
            category=cat,
            is_muted=aid in self.muted,
        )
    def get_unfollow_candidates(self) -> list[AccountScore]:
        res = [self._create(aid) for aid in (self.following - self.followers) if self.score(aid) == 0]
        return sorted(res, key=lambda x: (not x.is_muted, int(x.account_id)))
    def get_valuable_mutuals(self, limit: int | None = None) -> list[AccountScore]:
        lim = limit or self.config.limits.mutuals
        res = [self._create(aid) for aid in (self.following & self.followers)]
        return sorted(res, key=lambda x: x.score, reverse=True)[:lim]
    def get_all(self, limit: int = 0) -> list[AccountScore]:
        ids = set(self.followers) | set(self.following) | {i for c in self.counts.values() for i in c}
        res = sorted([self._create(aid) for aid in ids], key=lambda x: x.score, reverse=True)
        return res[:limit] if limit > 0 else res

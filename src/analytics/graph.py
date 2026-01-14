from typing import Dict, List


class GraphAnalytics:
    def __init__(self, followers: List[str], following: List[str]):
        self.followers = set(followers)
        self.following = set(following)

    def analyze_graph(self) -> Dict[str, any]:
        non_followers = self.following - self.followers
        fans = self.followers - self.following
        mutuals = self.following.intersection(self.followers)

        total_followers = len(self.followers)
        total_following = len(self.following)

        follow_back_rate = len(mutuals) / total_following * 100 if total_following else 0
        fan_ratio = len(fans) / total_followers * 100 if total_followers else 0
        follower_following_ratio = total_followers / total_following if total_following else 0

        return {
            "stats": {
                "total_followers": total_followers,
                "total_following": total_following,
                "non_followers_count": len(non_followers),
                "fans_count": len(fans),
                "mutuals_count": len(mutuals),
                "follow_back_rate": round(follow_back_rate, 1),
                "fan_ratio": round(fan_ratio, 1),
                "ff_ratio": round(follower_following_ratio, 2),
            },
            "non_followers_sample": list(non_followers)[:10],
            "fans_sample": list(fans)[:10],
        }

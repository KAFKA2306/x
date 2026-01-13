from typing import Dict, List


class GraphAnalytics:
    def __init__(self, followers: List[str], following: List[str]):
        self.followers = set(followers)
        self.following = set(following)

    def analyze_graph(self) -> Dict[str, any]:
        non_followers = self.following - self.followers

        fans = self.followers - self.following

        mutuals = self.following.intersection(self.followers)

        return {
            "stats": {
                "total_followers": len(self.followers),
                "total_following": len(self.following),
                "non_followers_count": len(non_followers),
                "fans_count": len(fans),
                "mutuals_count": len(mutuals),
            },
            "non_followers_sample": list(non_followers)[:10],
            "fans_sample": list(fans)[:10],
        }

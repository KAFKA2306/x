from collections import defaultdict
from typing import Dict, List

from src.models import Tweet


class EfficiencyAnalytics:
    def __init__(self, tweets: List[Tweet]):
        self.tweets = tweets

    def analyze_best_time(self) -> Dict[str, Dict[int, float]]:
        slots = defaultdict(lambda: defaultdict(lambda: [0, 0]))

        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for t in self.tweets:
            engagement = getattr(t, "favorite_count", 0) + getattr(t, "retweet_count", 0)

            day = weekdays[t.created_at.weekday()]
            hour = t.created_at.hour

            slots[day][hour][0] += engagement
            slots[day][hour][1] += 1

        result = {}
        for day in weekdays:
            result[day] = {}
            for hour in range(24):
                total_eng, count = slots[day][hour]
                result[day][hour] = round(total_eng / count, 2) if count > 0 else 0.0

        return result

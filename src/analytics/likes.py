from collections import Counter, defaultdict
from dataclasses import dataclass

from src.models import AppConfig, Like

LIKE_CATEGORIES: dict[str, list[str]] = {
    "VRChat_Avatar": ["アバター", "avatar", "アバタ改変", "shader"],
    "VRChat_World": ["ワールド", "world", "world紹介", "ワールド紹介"],
    "VRChat_Event": ["集会", "イベント", "event", "joinwars", "vket"],
    "VRChat_Photo": ["写真", "photo", "ss", "スクショ"],
    "VRChat_General": ["vrchat", "vrc"],
    "VR_Hardware": ["pico", "quest", "vision pro", "oculus", "valve index", "hmd"],
    "VR_Other": ["neosvr", "resonite", "mocopi", "フルトラ", "fullbody"],
    "BOOTH": ["booth", "で購入しました"],
    "Invest_Crypto": ["bitcoin", "btc", "ethereum", "eth", "crypto", "nft", "sol", "xrp"],
    "Invest_Stock": ["nvda", "tsla", "aapl", "株", "stock", "米国株", "earnings", "eps", "決算"],
    "Invest_FX": ["oanda", "fx", "為替", "ドル円", "usdjpy"],
    "Invest_REIT": ["reit", "不動産投資"],
    "Invest_General": ["投資", "invest", "trading", "ポートフォリオ"],
    "News_Finance": ["日本経済新聞", "日経", "nikkei", "bloomberg", "経済"],
    "AI_LLM": ["claude", "gpt", "chatgpt", "gemini", "llm", "openai", "anthropic"],
    "AI_Image": ["stablediffusion", "midjourney", "dalle", "aiイラスト", "aiart"],
    "AI_Code": ["copilot", "cursor", "cline", "programming", "コード"],
    "AI_Voice": ["vcclient", "ボイチェン", "rvc", "voice changer"],
    "BigTech": ["apple", "google", "meta", "microsoft", "amazon", "nvidia"],
    "Gaming": ["ゲーム", "game", "steam", "switch", "ps5", "シャドバ"],
    "Meme": ["現場猫", "ねこ", "cat", "にゃ", "わろた", "草"],
    "Science": ["化学", "science", "物理", "数学", "エビデンス"],
    "Music": ["音楽", "music", "spotify", "song", "bgm"],
    "Food": ["ご飯", "飯", "food", "ラーメン", "カレー", "美味し"],
    "Daily": ["おはよう", "おやすみ", "おつかれ", "おはよ"],
    "Note": ["note.com", "#note"],
    "Unavailable": ["unable to view", "suspended", "learnmore"],
}

CATEGORY_GROUPS: dict[str, list[str]] = {
    "VRChat": ["VRChat_Avatar", "VRChat_World", "VRChat_Event", "VRChat_Photo", "VRChat_General"],
    "VR_Tech": ["VR_Hardware", "VR_Other"],
    "Investment": ["Invest_Stock", "Invest_Crypto", "Invest_FX", "Invest_REIT", "Invest_General"],
    "AI": ["AI_LLM", "AI_Image", "AI_Code", "AI_Voice"],
    "News_Tech": ["News_Finance", "BigTech"],
    "Lifestyle": ["Gaming", "Music", "Food", "Daily", "Meme", "Science"],
    "Other": ["BOOTH", "Note", "Unavailable"],
}


@dataclass
class CategoryResult:
    name: str
    count: int
    percentage: float
    top_accounts: list[tuple[str, int]]


@dataclass
class LikesAnalysis:
    total: int
    categorized: int
    categorized_pct: float
    categories: list[CategoryResult]
    groups: dict[str, int]


def categorize_like(text: str) -> str:
    txt = text.lower()
    for cat, keywords in LIKE_CATEGORIES.items():
        if any(kw in txt for kw in keywords):
            return cat
    return "Uncategorized"


def analyze_likes(likes: list[Like], config: AppConfig) -> LikesAnalysis:
    results: dict[str, list[Like]] = defaultdict(list)
    for lk in likes:
        cat = categorize_like(lk.full_text)
        results[cat].append(lk)

    total = len(likes)
    categorized = sum(len(v) for k, v in results.items() if k != "Uncategorized")

    cat_results = [
        CategoryResult(
            name=cat,
            count=len(items),
            percentage=round(len(items) / total * 100, 1),
            top_accounts=Counter(m for lk in items for m in lk.mentions).most_common(5),
        )
        for cat in LIKE_CATEGORIES
        if (items := results.get(cat, []))
    ]
    cat_results.sort(key=lambda x: x.count, reverse=True)

    groups = {}
    for group, cats in CATEGORY_GROUPS.items():
        groups[group] = sum(len(results.get(c, [])) for c in cats)
    groups["Uncategorized"] = len(results.get("Uncategorized", []))

    return LikesAnalysis(
        total=total,
        categorized=categorized,
        categorized_pct=round(categorized / total * 100, 1) if total else 0,
        categories=cat_results,
        groups=groups,
    )


@dataclass
class TopicCluster:
    id: int
    size: int
    keywords: list[str]
    samples: list[str]


def cluster_likes(likes: list[Like], n_clusters: int = 10) -> list[TopicCluster]:
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer

    texts = [lk.full_text for lk in likes if len(lk.full_text) > 10]
    if len(texts) < n_clusters:
        return []

    vectorizer = TfidfVectorizer(max_features=1000, stop_words="english", min_df=5)
    tfidf = vectorizer.fit_transform(texts)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(tfidf)

    feature_names = vectorizer.get_feature_names_out()
    clusters = []

    for i in range(n_clusters):
        indices = [j for j, label in enumerate(labels) if label == i]
        center = kmeans.cluster_centers_[i]
        top_indices = center.argsort()[-10:][::-1]
        clusters.append(
            TopicCluster(
                id=i,
                size=len(indices),
                keywords=[feature_names[idx] for idx in top_indices],
                samples=[texts[j][:100] for j in indices[:3]],
            )
        )
    return sorted(clusters, key=lambda x: x.size, reverse=True)

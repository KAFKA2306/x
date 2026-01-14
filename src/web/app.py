import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from src.analytics.audience import AudienceAnalytics
from src.analytics.efficiency import EfficiencyAnalytics
from src.analytics.graph import GraphAnalytics
from src.analytics.interests import analyze_likes_interests, analyze_tweets_interests
from src.analytics.recommendations import RecommendationAnalytics, extract_interaction_counts
from src.config import load_config
from src.exporters import export_account_scores_to_csv
from src.features import analyze_tweets
from src.loader import extract_user_map, load_likes, load_tweets, load_user_list

app = FastAPI()
templates = Jinja2Templates(directory="src/web/templates")
config = load_config()

if not os.path.exists(config.files.tweets):
    tweets = []
    analysis = None
else:
    tweets = load_tweets(config.files.tweets)
    analysis = analyze_tweets(tweets, config)

followers = load_user_list(config.files.follower)
following = load_user_list(config.files.following)
likes = load_likes(config.files.like) if os.path.exists(config.files.like) else []

audience_analytics = AudienceAnalytics(tweets, config) if tweets else None
efficiency_analytics = EfficiencyAnalytics(tweets) if tweets else None
graph_analytics = GraphAnalytics(followers, following)
likes_interests = analyze_likes_interests(likes, config) if likes else None
tweets_interests = analyze_tweets_interests(tweets, config) if tweets else None

if tweets:
    user_map = extract_user_map(config.files.tweets)
    reply_counts, retweet_counts, mention_counts, like_counts = extract_interaction_counts(
        tweets, likes, user_map, config
    )
    recommendation_analytics = RecommendationAnalytics(
        config,
        set(followers),
        set(following),
        reply_counts,
        retweet_counts,
        mention_counts,
        like_counts,
        user_map,
    )
else:
    recommendation_analytics = None


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request, "analysis": analysis, "config": config})


@app.get("/audience", response_class=HTMLResponse)
async def get_audience_insights(request: Request) -> HTMLResponse:
    if not audience_analytics:
        return HTMLResponse("<p>No data available</p>")

    stats = audience_analytics.analyze_interactions()
    return templates.TemplateResponse("partials/audience.html", {"request": request, "stats": stats})


@app.get("/efficiency", response_class=HTMLResponse)
async def get_efficiency_heatmap(request: Request) -> HTMLResponse:
    if not efficiency_analytics:
        return HTMLResponse("<p>No data available</p>")

    heatmap = efficiency_analytics.analyze_best_time()
    return templates.TemplateResponse("partials/efficiency.html", {"request": request, "heatmap": heatmap})


@app.get("/graph", response_class=HTMLResponse)
async def get_graph_stats(request: Request) -> HTMLResponse:
    stats = graph_analytics.analyze_graph()
    return templates.TemplateResponse("partials/graph.html", {"request": request, "graph": stats})


@app.get("/interests", response_class=HTMLResponse)
async def get_interests_stats(request: Request) -> HTMLResponse:
    if not likes_interests and not tweets_interests:
        return HTMLResponse("<p>No data available</p>")

    return templates.TemplateResponse(
        "partials/interests.html",
        {
            "request": request,
            "likes": likes_interests,
            "tweets": tweets_interests,
        },
    )


@app.get("/recommendations", response_class=HTMLResponse)
async def get_recommendations(request: Request) -> HTMLResponse:
    if not recommendation_analytics:
        return HTMLResponse("<p>No data available</p>")

    candidates = recommendation_analytics.get_unfollow_candidates()
    mutuals = recommendation_analytics.get_valuable_mutuals()
    return templates.TemplateResponse(
        "partials/recommendations.html",
        {
            "request": request,
            "candidates": candidates,
            "mutuals": mutuals,
        },
    )


@app.get("/recommendations/download", response_class=PlainTextResponse)
async def download_recommendations_csv() -> PlainTextResponse:
    if not recommendation_analytics:
        return PlainTextResponse("No data available")

    candidates = recommendation_analytics.get_unfollow_candidates()
    csv_content = export_account_scores_to_csv(candidates)

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=unfollow_candidates.csv"},
    )


@app.get("/recommendations/download_mutuals", response_class=PlainTextResponse)
async def download_mutuals_csv() -> PlainTextResponse:
    if not recommendation_analytics:
        return PlainTextResponse("No data available")

    mutuals = recommendation_analytics.get_valuable_mutuals(limit=0)
    csv_content = export_account_scores_to_csv(mutuals)

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=valuable_mutuals.csv"},
    )


@app.get("/tweets/download", response_class=PlainTextResponse)
async def download_tweets_csv() -> PlainTextResponse:
    if not tweets:
        return PlainTextResponse("No data available")

    from src.exporters import export_tweets_to_csv

    csv_content = export_tweets_to_csv(tweets)

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=all_tweets.csv"},
    )


@app.get("/interactions/download", response_class=PlainTextResponse)
async def download_interactions_csv() -> PlainTextResponse:
    if not recommendation_analytics:
        return PlainTextResponse("No data available")

    interactions = recommendation_analytics.get_all_interactions()
    csv_content = export_account_scores_to_csv(interactions)

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=all_interactions.csv"},
    )


def start_server() -> None:
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["src", "data"])

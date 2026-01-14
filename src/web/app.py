import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.analytics.audience import AudienceAnalytics
from src.analytics.efficiency import EfficiencyAnalytics
from src.analytics.graph import GraphAnalytics
from src.analytics.interests import analyze_likes_interests, analyze_tweets_interests
from src.config import load_config
from src.features import analyze_tweets
from src.loader import load_likes, load_tweets, load_user_list

app = FastAPI()
templates = Jinja2Templates(directory="src/web/templates")
config = load_config()

if not os.path.exists(config.input_file):
    tweets = []
    analysis = None
else:
    tweets = load_tweets(config.input_file)
    analysis = analyze_tweets(tweets)

data_dir = os.path.dirname(config.input_file)
followers_file = os.path.join(data_dir, "follower.js")
following_file = os.path.join(data_dir, "following.js")
like_file = os.path.join(data_dir, "like.js")

followers = load_user_list(followers_file)
following = load_user_list(following_file)
likes = load_likes(like_file) if os.path.exists(like_file) else []

mentioned_users = set()
for t in tweets:
    mentioned_users.update(t.mentions)

audience_analytics = AudienceAnalytics(tweets) if tweets else None
efficiency_analytics = EfficiencyAnalytics(tweets) if tweets else None
graph_analytics = GraphAnalytics(followers, following, mentioned_users)
likes_interests = analyze_likes_interests(likes) if likes else None
tweets_interests = analyze_tweets_interests(tweets) if tweets else None


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "analysis": analysis, "config": config})


@app.get("/audience", response_class=HTMLResponse)
async def get_audience_insights(request: Request):
    if not audience_analytics:
        return "<p>No data available</p>"

    stats = audience_analytics.analyze_interactions()
    return templates.TemplateResponse("partials/audience.html", {"request": request, "stats": stats})


@app.get("/efficiency", response_class=HTMLResponse)
async def get_efficiency_heatmap(request: Request):
    if not efficiency_analytics:
        return "<p>No data available</p>"

    heatmap = efficiency_analytics.analyze_best_time()
    return templates.TemplateResponse("partials/efficiency.html", {"request": request, "heatmap": heatmap})


@app.get("/graph", response_class=HTMLResponse)
async def get_graph_stats(request: Request):
    stats = graph_analytics.analyze_graph()
    return templates.TemplateResponse("partials/graph.html", {"request": request, "graph": stats})


@app.get("/interests", response_class=HTMLResponse)
async def get_interests_stats(request: Request):
    if not likes_interests and not tweets_interests:
        return "<p>No data available</p>"

    return templates.TemplateResponse("partials/interests.html", {
        "request": request,
        "likes": likes_interests,
        "tweets": tweets_interests,
    })





def start_server():
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)

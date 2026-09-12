import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from src.analytics.core import (
    analyze_efficiency_core,
    analyze_graph_core,
    analyze_interests,
    analyze_tweets_core,
)
from src.analytics.likes import analyze_likes, cluster_likes
from src.analytics.profiling import analyze_profile
from src.analytics.recommendations import RecommendationAnalytics, extract_interactions
from src.config import load_config
from src.exporters import export_account_scores_to_csv, export_tweets_to_csv
from src.input_readiness import load_configured_inputs

app = FastAPI()
templates = Jinja2Templates(directory="src/web/templates")
config = load_config()
input_state = load_configured_inputs(config)

tweets = input_state.data.get("tweets", []) if input_state.ready else []
fers = input_state.data.get("follower", []) if input_state.ready else []
fing = input_state.data.get("following", []) if input_state.ready else []
likes = input_state.data.get("like", []) if input_state.ready else []
mutes = input_state.data.get("mute", set()) if input_state.ready else set()
ans = analyze_tweets_core(tweets, config) if input_state.ready and tweets else None

if input_state.ready and tweets:
    umap = {}
    ids_cnt, hts = extract_interactions(tweets, likes, umap, config)
    ra = RecommendationAnalytics(config, set(fers), set(fing), ids_cnt, umap, mutes)
else:
    ra = None


@app.middleware("http")
async def require_ready_inputs(request: Request, call_next):
    if request.url.path == "/readiness" or input_state.ready:
        return await call_next(request)
    return JSONResponse(input_state.as_dict(), status_code=503)


@app.get("/readiness")
async def readiness():
    return JSONResponse(input_state.as_dict(), status_code=200 if input_state.ready else 503)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "analysis": ans, "config": config})


@app.get("/audience", response_class=HTMLResponse)
async def get_audience_insights(request: Request):
    if not ra:
        return HTMLResponse("<p>No data available</p>")
    from src.models import InteractionStats

    def map_n(counts):
        return [(ra.account_map.get(aid, aid), c) for aid, c in counts]

    stats = InteractionStats(
        top_replied=map_n(ra.counts["reply"].most_common(config.limits.top_stats)),
        top_retweeted=map_n(ra.counts["retweet"].most_common(config.limits.top_stats)),
        top_hashtags=hts.most_common(config.limits.top_stats),
        top_mentions=map_n(ra.counts["mention"].most_common(config.limits.top_stats)),
        total_replies=sum(ra.counts["reply"].values()),
        total_retweets=sum(ra.counts["retweet"].values()),
    )
    return templates.TemplateResponse("partials/audience.html", {"request": request, "stats": stats})


@app.get("/efficiency", response_class=HTMLResponse)
async def get_efficiency_heatmap(request: Request):
    if not tweets:
        return HTMLResponse("<p>No data available</p>")
    return templates.TemplateResponse(
        "partials/efficiency.html",
        {"request": request, "heatmap": analyze_efficiency_core(tweets)},
    )


@app.get("/graph", response_class=HTMLResponse)
async def get_graph_stats(request: Request):
    return templates.TemplateResponse(
        "partials/graph.html", {"request": request, "graph": analyze_graph_core(fers, fing)}
    )


@app.get("/interests", response_class=HTMLResponse)
async def get_interests_stats(request: Request):
    if not likes and not tweets:
        return HTMLResponse("<p>No data available</p>")
    return templates.TemplateResponse(
        "partials/interests.html",
        {
            "request": request,
            "likes": analyze_interests([lk.full_text for lk in likes], config) if likes else None,
            "tweets": {
                "original": analyze_interests([t.full_text for t in tweets if t.is_original], config),
                "retweets": analyze_interests([t.full_text for t in tweets if t.is_retweet], config),
                "replies": analyze_interests([t.full_text for t in tweets if t.is_reply], config),
            }
            if tweets
            else None,
        },
    )


@app.get("/recommendations", response_class=HTMLResponse)
async def get_recommendations(request: Request):
    if not ra:
        return HTMLResponse("<p>No data available</p>")
    return templates.TemplateResponse(
        "partials/recommendations.html",
        {
            "request": request,
            "candidates": ra.get_unfollow_candidates(),
            "mutuals": ra.get_valuable_mutuals(),
        },
    )


def csv_response(data: str, filename: str):
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return PlainTextResponse(data, media_type="text/csv", headers=headers)


@app.get("/recommendations/download")
async def dl_rec():
    return csv_response(export_account_scores_to_csv(ra.get_unfollow_candidates()), "unfollow.csv")


@app.get("/recommendations/download_mutuals")
async def dl_mut():
    return csv_response(export_account_scores_to_csv(ra.get_valuable_mutuals(0)), "mutuals.csv")


@app.get("/tweets/download")
async def dl_tw():
    return csv_response(export_tweets_to_csv(tweets), "tweets.csv")


@app.get("/interactions/download")
async def dl_int():
    return csv_response(export_account_scores_to_csv(ra.get_all()), "interactions.csv")


@app.get("/profile", response_class=HTMLResponse)
async def get_profile(request: Request):
    if not tweets:
        return HTMLResponse("<p>No data available</p>")
    return templates.TemplateResponse(
        "partials/profile.html", {"request": request, "profile": analyze_profile(tweets, config)}
    )


@app.get("/likes", response_class=HTMLResponse)
async def get_likes_analysis(request: Request):
    if not likes:
        return HTMLResponse("<p>No data available</p>")
    return templates.TemplateResponse(
        "partials/likes.html", {"request": request, "analysis": analyze_likes(likes, config)}
    )


@app.get("/likes/clusters", response_class=HTMLResponse)
async def get_likes_clusters(request: Request):
    if not likes:
        return HTMLResponse("<p>No data available</p>")
    return templates.TemplateResponse("partials/clusters.html", {"request": request, "clusters": cluster_likes(likes)})


def start_server():
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)

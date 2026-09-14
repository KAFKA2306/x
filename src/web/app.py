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
from src.loader import load_archive_inputs

app = FastAPI()
templates = Jinja2Templates(directory="src/web/templates")
config = load_config()
archive_inputs = load_archive_inputs(config)

tweets = archive_inputs.tweets if archive_inputs.analysis_ready else []
fers = archive_inputs.follower if archive_inputs.analysis_ready else []
fing = archive_inputs.following if archive_inputs.analysis_ready else []
likes = archive_inputs.like if archive_inputs.analysis_ready else []
mutes = archive_inputs.mute if archive_inputs.analysis_ready else set()
ans = analyze_tweets_core(tweets, config) if tweets else None

if tweets:
    umap = {}
    ids_cnt, hts = extract_interactions(tweets, likes, umap, config)
    ra = RecommendationAnalytics(config, set(fers), set(fing), ids_cnt, umap, mutes)
else:
    hts = None
    ra = None


def _readiness_payload() -> dict:
    return {
        "analysis_ready": archive_inputs.analysis_ready,
        "inputs": {
            name: {
                "path": item.path,
                "required": item.required,
                "status": item.status.value,
                "error": item.error,
            }
            for name, item in archive_inputs.readiness.items()
        },
    }


def _not_ready_response():
    if archive_inputs.analysis_ready:
        return None
    return JSONResponse(_readiness_payload(), status_code=503)


@app.get("/readiness")
async def readiness():
    status_code = 200 if archive_inputs.analysis_ready else 503
    return JSONResponse(_readiness_payload(), status_code=status_code)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    blocked = _not_ready_response()
    if blocked:
        return blocked
    return templates.TemplateResponse("dashboard.html", {"request": request, "analysis": ans, "config": config})


@app.get("/audience", response_class=HTMLResponse)
async def get_audience_insights(request: Request):
    blocked = _not_ready_response()
    if blocked:
        return blocked
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
    blocked = _not_ready_response()
    if blocked:
        return blocked
    if not tweets:
        return HTMLResponse("<p>No data available</p>")
    return templates.TemplateResponse(
        "partials/efficiency.html",
        {"request": request, "heatmap": analyze_efficiency_core(tweets)},
    )


@app.get("/graph", response_class=HTMLResponse)
async def get_graph_stats(request: Request):
    blocked = _not_ready_response()
    if blocked:
        return blocked
    return templates.TemplateResponse(
        "partials/graph.html", {"request": request, "graph": analyze_graph_core(fers, fing)}
    )


@app.get("/interests", response_class=HTMLResponse)
async def get_interests_stats(request: Request):
    blocked = _not_ready_response()
    if blocked:
        return blocked
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
    blocked = _not_ready_response()
    if blocked:
        return blocked
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
    blocked = _not_ready_response()
    if blocked:
        return blocked
    if not ra:
        return HTMLResponse("<p>No data available</p>", status_code=409)
    return csv_response(export_account_scores_to_csv(ra.get_unfollow_candidates()), "unfollow.csv")


@app.get("/recommendations/download_mutuals")
async def dl_mut():
    blocked = _not_ready_response()
    if blocked:
        return blocked
    if not ra:
        return HTMLResponse("<p>No data available</p>", status_code=409)
    return csv_response(export_account_scores_to_csv(ra.get_valuable_mutuals(0)), "mutuals.csv")


@app.get("/tweets/download")
async def dl_tw():
    blocked = _not_ready_response()
    if blocked:
        return blocked
    return csv_response(export_tweets_to_csv(tweets), "tweets.csv")


@app.get("/interactions/download")
async def dl_int():
    blocked = _not_ready_response()
    if blocked:
        return blocked
    if not ra:
        return HTMLResponse("<p>No data available</p>", status_code=409)
    return csv_response(export_account_scores_to_csv(ra.get_all()), "interactions.csv")


@app.get("/profile", response_class=HTMLResponse)
async def get_profile(request: Request):
    blocked = _not_ready_response()
    if blocked:
        return blocked
    if not tweets:
        return HTMLResponse("<p>No data available</p>")
    return templates.TemplateResponse(
        "partials/profile.html", {"request": request, "profile": analyze_profile(tweets, config)}
    )


@app.get("/likes", response_class=HTMLResponse)
async def get_likes_analysis(request: Request):
    blocked = _not_ready_response()
    if blocked:
        return blocked
    if not likes:
        return HTMLResponse("<p>No data available</p>")
    return templates.TemplateResponse(
        "partials/likes.html", {"request": request, "analysis": analyze_likes(likes, config)}
    )


@app.get("/likes/clusters", response_class=HTMLResponse)
async def get_likes_clusters(request: Request):
    blocked = _not_ready_response()
    if blocked:
        return blocked
    if not likes:
        return HTMLResponse("<p>No data available</p>")
    return templates.TemplateResponse("partials/clusters.html", {"request": request, "clusters": cluster_likes(likes)})


def start_server():
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, reload=True)

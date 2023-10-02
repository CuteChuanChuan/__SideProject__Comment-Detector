import enum
import uvicorn
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.wsgi import WSGIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
from dash_app_keyword import create_keyword_dash_app
from dash_app_overview import create_overview_dash_app
from dash_app_commenter import create_commenter_dash_app
from utils_dashboard import utils_mongodb as op_mongo

app = FastAPI(
    title="PTT Comment Detector",
    version="0.1.0",
    summary="PTT Comment Detector is a tool to provide users information "
            "for judging credibility of comments on PTT (The largest forum in Taiwan).",
)
templates = Jinja2Templates(directory="templates")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class AllowedBoard(str, enum.Enum):
    gossip = "gossip"
    politics = "politics"


@app.get(path="/", response_class=HTMLResponse)
def home(request: Request):
    data = {"page": "Home Page"}
    return templates.TemplateResponse("index.html", {"request": request, "data": data})


@app.get(
    path="/commenters/{commenter_id}",
    summary="Get all articles in a board specified which have been commented by a commenter",
)
@limiter.limit("3/minute")
def get_commenter_articles(
    request: Request,
    commenter_id: str,
    target_collection: AllowedBoard = Query(default_value="gossip",
                                            description="Target collection name can only be 'gossip' or 'politics'",
                                            default="gossip",)
):
    all_articles = op_mongo.extract_all_articles_commenter_involved(
        target_collection, commenter_id
    )
    return {
        "commenter_id": commenter_id,
        "board": target_collection,
        "num_articles_commented": len(all_articles),
        "articles": all_articles,
    }


@app.get(
    path="/authors/{author_id}",
    summary="Get top 20 articles ordered by number of comments descending published by a author",
)
@limiter.limit("3/minute")
def get_author_articles(
    request: Request,
    author_id: str,
    target_collection: AllowedBoard = Query(
        default_value="gossip",
        description="Target collection name can only be 'gossip' or 'politics'.",
        default="gossip",
    ),
):
    """
    author_id: Please only enter author account id without space and brackets (e.g., ABC (Nickname) -> please only enter ABC)
    """
    if len(author_id.split(" ")) != 1:
        return {
            "error": "Please only enter author account id without space and brackets (e.g., ABC (Nickname) "
                     "-> please only enter ABC)"
        }
    all_articles = op_mongo.extract_top_n_articles_author_published(
        target_collection, author_id, num_articles=20
    )
    return {
        "author_id": author_id,
        "board": target_collection,
        "num_articles_published": len(all_articles),
        "articles": all_articles,
    }


@app.get(
    path="/articles/{keyword}",
    summary="Get top 20 articles ordered by number of comments descending which have the keyword",
)
@limiter.limit("3/minute")
def get_articles_by_keyword(
    request: Request,
    keyword: str,
    target_collection: AllowedBoard = Query(
        default_value="gossip",
        description="Target collection name can only be 'gossip' or 'politics'.",
        default="gossip",
    ),
):
    all_articles = op_mongo.extract_top_n_articles_keyword_in_title(
        target_collection=target_collection, keyword=keyword, num_articles=20
    )
    return {
        "keyword": keyword,
        "board": target_collection,
        "num_articles": len(all_articles),
        "articles": all_articles,
    }


@app.get(
    path="/ipaddress/{ipaddress}",
    summary="Get all commenters in a board specified which have used the same ipaddress",
)
@limiter.limit("3/minute")
def get_commenter_ids_by_ipaddress(
    request: Request,
    ipaddress: str,
    target_collection: AllowedBoard = Query(
        default_value="gossip",
        description="Target collection name can only be 'gossip' or 'politics'.",
        default="gossip",
    )
):
    all_commenters_id = op_mongo.extract_commenters_id_using_same_ipaddress(
        target_collection, ipaddress
    )
    return {
        "ipaddress": ipaddress,
        "board": target_collection,
        "num_commenters": len(all_commenters_id),
        "commenters": all_commenters_id,
    }


overview_app = create_overview_dash_app(requests_pathname_prefix="/overview/")
app.mount("/overview", WSGIMiddleware(overview_app.server))

keyword_app = create_keyword_dash_app(requests_pathname_prefix="/keyword/")
app.mount("/keyword", WSGIMiddleware(keyword_app.server))

commenter_app = create_commenter_dash_app(requests_pathname_prefix="/commenter/")
app.mount("/commenter", WSGIMiddleware(commenter_app.server))


if __name__ == "__main__":
    uvicorn.run(app, port=8000, host="0.0.0.0")

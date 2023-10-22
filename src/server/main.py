import os
import enum
import redis
import uvicorn
from fastapi.responses import HTMLResponse, RedirectResponse
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

# Connect to redis as long as users enter the home page
# so that when they visit the trend page, the data of crawled articles can be shown immediately
# rather than reloading the whole page
redis_pool = redis.ConnectionPool(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    db=os.getenv("REDIS_DB", 0),
    password=os.getenv("REDIS_PASSWORD", None),
    socket_timeout=10,
    socket_connect_timeout=10,
)
redis_conn = redis.StrictRedis(connection_pool=redis_pool, decode_responses=True)


class AllowedBoard(str, enum.Enum):
    gossip = "gossip"
    politics = "politics"


@app.get(path="/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    return RedirectResponse("/dashboard")


@app.get(
    path="/commenters/{commenter_id}",
    summary="Get all articles in a board specified which have been commented by a commenter",
)
@limiter.limit("3/minute")
def get_commenter_articles(
    request: Request,
    commenter_id: str,
    target_collection: AllowedBoard = Query(
        default_value="gossip",
        description="Target collection name can only be 'gossip' or 'politics'",
        default="gossip",
    ),
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
    ),
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


@app.get(path="/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    html_content = """
        <!DOCTYPE html>
            <html lang="en">
            
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Dashboard</title>
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css" />
                <style>
                    .nav-link {
                        font-size: 1.1rem; /* Increase the font size */
                    }
                </style>
            </head>
            
            <body>
                <div class="container mt-5 mb-5">
                    <h1 class="text-center mb-5 animate__animated animate__bounce">PTT Comment Detector</h1>
                    <div class="d-flex justify-content-center animate__animated animate__fadeIn mb-3">
                        <nav class="navbar navbar-expand-lg navbar-light bg-light rounded">
                            <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                                <span class="navbar-toggler-icon"></span>
                            </button>
                            <div class="collapse navbar-collapse" id="navbarNav">
                                <ul class="navbar-nav">
                                    <li class="nav-item">
                                        <a class="nav-link" href="/overview">  趨勢分析  </a>
                                    </li>
                                    <li class="nav-item">
                                        <a class="nav-link" href="/keyword">  關鍵字分析  </a>
                                    </li>
                                    <li class="nav-item">
                                        <a class="nav-link" href="/commenter">  留言者分析  </a>
                                    </li>
                                    <li class="nav-item"> <!-- New button -->
                                        <a class="nav-link" href="/docs">  開源資料 API  </a>
                                    </li>
                                </ul>
                            </div>
                        </nav>
                    </div>
            
                    <!-- Five dots in the middle -->
                    <br>
                    <div class="d-flex justify-content-center flex-column align-items-center">
                        <h3>關於</h3>
                        <br>
                        <p class="mb-2">PTT 是臺灣最大的論壇平臺，然而疑似網軍與帶風向的情況層出不窮，為了幫助使用者可以有更好的媒體識讀與判讀</p>
                        <p class="mb-2">PTT Comment Detector 將焦點鎖定在八卦版 (使用人數最多) & 政黑板 (政治評論相關)</p>
                        <p class="mb-2">每十分鐘收集文章與留言資料，自動整理成客觀的資訊，並且從不同面向切入，讓使用者可以在各個分析儀表板自由探索</p>
                        <p class="mb-2">PTT Comment Detector 也提供 API 將收集到的資料開放給有興趣使用的人</p>
                        <br>
                        <p class="mb-2">趨勢分析：了解當前議題</p>
                        <p class="mb-2">關鍵字分析：了解關鍵字與留言者間的關係</p>
                        <p class="mb-2">留言者分析：了解特定留言者</p>
                        <p class="mb-2">開源資料 API：獲得更多資訊 (例如：IP 與作者等)</p>
                    </div>

                </div>
            
                <!-- Bootstrap and jQuery Scripts -->
                <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.3/dist/umd/popper.min.js"></script>
                <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
            </body>
            
            </html>

    """
    return HTMLResponse(content=html_content)


overview_app = create_overview_dash_app(requests_pathname_prefix="/overview/")
app.mount("/overview", WSGIMiddleware(overview_app.server))

keyword_app = create_keyword_dash_app(requests_pathname_prefix="/keyword/")
app.mount("/keyword", WSGIMiddleware(keyword_app.server))

commenter_app = create_commenter_dash_app(requests_pathname_prefix="/commenter/")
app.mount("/commenter", WSGIMiddleware(commenter_app.server))


if __name__ == "__main__":
    uvicorn.run(app, port=8000, host="0.0.0.0")

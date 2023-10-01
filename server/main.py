import enum
import uvicorn
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.wsgi import WSGIMiddleware
from dash_app_keyword import create_keyword_dash_app
from dash_app_overview import create_overview_dash_app
from dash_app_commenter import create_commenter_dash_app
from utils_dashboard import utils_mongodb as op_accounts

app = FastAPI()
templates = Jinja2Templates(directory="templates")


class AllowedBoard(str, enum.Enum):
    gossip = "gossip"
    politic = "politic"


@app.get(
    path="/",
    response_class=HTMLResponse

)
def home(request: Request):
    data = {
        "page": "Home Page"
    }
    return templates.TemplateResponse("index.html", {"request": request, "data": data})


@app.get(
    path="/commenters/{commenter_id}",
    summary="Get all articles in a board specified which have been commented by a commenter",
)
def get_commenter_articles(
    commenter_id: str,
    target_collection: AllowedBoard = Query(
        default_value="gossip",
        description="Target collection name can only be 'gossip' or 'politic'",
    ),
):
    all_articles = op_accounts.extract_all_articles_commenter_involved(
        target_collection, commenter_id
    )
    return {
        "commenter_id": commenter_id,
        "board": target_collection,
        "articles": all_articles,
    }


@app.get(
    path="/authors/{author_id}",
    summary="Get top 20 articles ordered by number of comments descending published by a author"
)
def get_top_20_articles(author_id: str):
    return


overview_app = create_overview_dash_app(requests_pathname_prefix="/overview/")
app.mount("/overview", WSGIMiddleware(overview_app.server))

keyword_app = create_keyword_dash_app(requests_pathname_prefix="/keyword/")
app.mount("/keyword", WSGIMiddleware(keyword_app.server))

commenter_app = create_commenter_dash_app(requests_pathname_prefix="/commenter/")
app.mount("/commenter", WSGIMiddleware(commenter_app.server))


if __name__ == "__main__":
    uvicorn.run(app, port=8001)

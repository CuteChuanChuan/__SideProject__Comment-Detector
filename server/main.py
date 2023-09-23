import enum
import uvicorn
from dash_app import create_dash_app
from fastapi import FastAPI, Query
from fastapi.middleware.wsgi import WSGIMiddleware
import utils_mongodb as op_accounts


app = FastAPI()


class AllowedBoard(str, enum.Enum):
    gossip = "gossip"
    politic = "politic"


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


dash_app = create_dash_app(requests_pathname_prefix="/dash/")
app.mount("/dash", WSGIMiddleware(dash_app.server))


if __name__ == "__main__":
    uvicorn.run(app, port=8001)

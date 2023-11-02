import dash
import jieba.analyse
from dotenv import load_dotenv
from flask_caching import Cache
from dash import dcc, html, Input, Output
from collections import defaultdict
import dash_bootstrap_components as dbc

from utils_dashboard.config_dashboard import db
from utils_dashboard.plot_generate_concurrency_network import (
    preparation_network_graph,
    generate_concurrency_network_data,
    create_network_graph,
)
from utils_dashboard.utils_mongodb import (
    extract_top_freq_commenter_id,
    extract_top_agree_commenter_id,
    extract_top_disagree_commenter_id,
    extract_author_info_from_articles_title_having_keywords,
    extract_commenter_info_from_article_with_article_url,
    summarize_commenters_metadata,
    convert_commenters_metadata_to_dataframe,
)

load_dotenv(verbose=True)

DICT_FILE = "utils_dashboard/tc_dict.txt"
STOP_FILE = "utils_dashboard/stopwords.txt"
TC_FONT_PATH = "utils_dashboard/NotoSerifTC-Regular.otf"

jieba.set_dictionary(DICT_FILE)
jieba.analyse.set_stop_words(STOP_FILE)
TIMEOUT = 40
NUM_ARTICLES = 100
NUM_COMMENTERS = 5
NUM_NETWORK_COMMENTERS = 20

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]


def keyword_no_result_figure():
    return {
        "layout": {
            "xaxis": {"visible": False, "range": [0, 1]},
            "yaxis": {"visible": False, "range": [0, 1]},
            "annotations": [
                {
                    "text": "查無資料",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20},
                }
            ],
        }
    }


def create_keyword_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
    app = dash.Dash(
        __name__,
        requests_pathname_prefix=requests_pathname_prefix,
        external_stylesheets=[dbc.themes.MATERIA],
    )
    app.scripts.config.serve_locally = True
    cache = Cache(
        app.server,
        config={
            "CACHE_TYPE": "filesystem",
            "CACHE_DIR": "cache-directory",
            "CACHE_DEFAULT_TIMEOUT": TIMEOUT,
            "CACHE_THRESHOLD": 500,
        },
    )
    app.config.suppress_callback_exceptions = True
    dcc._js_dist[0]["external_url"] = "https://cdn.plot.ly/plotly-basic-latest.min.js"

    app.layout = dbc.Container(
        [
            html.H1("PTT Comment Detector - 關鍵字分析", className="text-center mb-4"),
            html.Div(
                [
                    html.A(
                        dbc.Button(
                            "關於",
                            outline=True,
                            color="primary",
                            className="ml-20",
                            style={"color": "gray"},
                        ),
                        href="/dashboard",
                        style={"marginRight": "15px"},
                    ),
                    html.A(
                        dbc.Button(
                            "趨勢分析",
                            outline=True,
                            color="primary",
                            className="mr-20",
                            style={"color": "gray"},
                        ),
                        href="/overview",
                        style={"marginRight": "15px"},
                    ),
                    html.A(
                        dbc.Button(
                            "關鍵字分析",
                            outline=True,
                            color="primary",
                            className="mr-20",
                            style={"color": "black", "font-weight": "bold"},
                        ),
                        style={"marginRight": "15px"},
                    ),
                    html.A(
                        dbc.Button(
                            "留言者分析",
                            outline=True,
                            color="primary",
                            className="ml-20",
                            style={"color": "gray"},
                        ),
                        href="/commenter",
                        style={"marginRight": "15px"},
                    ),
                    html.A(
                        dbc.Button(
                            "開源資料 API",
                            outline=True,
                            color="primary",
                            className="ml-20",
                            style={"color": "gray"},
                        ),
                        href="/docs",
                    ),
                ],
                style={"textAlign": "center"},
            ),
            html.Hr(),
            html.H5(
                f"關鍵字搜尋",
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Input(
                                id="keyword-search",
                                type="text",
                                value="",
                                placeholder="請輸入關鍵字",
                            ),
                        ],
                        width=2,
                        className="mb-2 ml-4",
                        style={"marginRight": "10px"},
                    ),
                    dbc.Col(
                        [
                            dcc.Dropdown(
                                id="dropdown-collection",
                                options=[
                                    {"label": "八卦版", "value": "gossip"},
                                    {"label": "政黑版", "value": "politics"},
                                ],
                                value="gossip",
                            ),
                        ],
                        width=2,
                        className="mb-2 mr-20",
                    ),
                    dbc.Col(
                        [
                            html.Button(
                                "確認",
                                id="submit-button-keyword",
                                disabled=False,
                            ),
                        ],
                        width=4,
                        className="mb-2",
                    ),
                ],
                className="mb-3",
            ),
            html.Hr(),
            html.H5(f"有關這個關鍵字的文章，最活躍的留言者為：", className="mb-3"),
            html.H6(
                "(說明：此部分是考量所有與關鍵字有關的文章，因此此處呈現的留言者不一定會在下方留言數量前100名中的文章中留言)",
                className="mb-3",
            ),
            html.H6(
                "(說明：留言共有三種類型，分別為：推、-> (單純回文)、噓)",
                className="mb-3",
            ),
            dcc.Loading(
                id="loading-keyword-info",
                type="circle",
                children=[
                    html.Div(id="keyword-freq", className="mt-3"),
                    html.Div(id="keyword-agree", className="mt-3"),
                    html.Div(id="keyword-disagree", className="mt-3"),
                ],
            ),
            html.Br(),
            html.Hr(),
            html.H5(
                f"活躍留言者一起留言的關係圖 (Concurrency Analysis)：",
                className="mb-3",
            ),
            html.H6(
                "(概念：網軍或是帶風向的人通常會比較活躍，也會利用從眾心態，一起在共同的文章中留言，來影響其他人的看法)",
                className="mb-3",
            ),
            html.H6(
                "(分析步驟 1 [活躍程度]：針對留言數最多的前100篇文章，找出推/噓文次數前20名的留言者)",
                className="mb-3",
            ),
            html.H6(
                "(分析步驟 2 [共同出現]：針對這些留言者，檢視他們在這100篇文章中一起留言的次數)",
                className="mb-3",
            ),
            html.H6(
                "(解讀 1：紅點是留言者，紅點間的藍線是兩個留言者共同留言的次數，藍線越粗越深代表共同出現次數越多)",
                className="mb-3",
            ),
            html.H6(
                "(解讀 2：可以將焦點鎖定在經常一起出現的留言者，並搭配分析個別留言者的行為特徵與開源資料API中的IP地址分析來綜合檢視，最終給出您自己心中的判斷)",
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Loading(
                            id="loading-network-like-graph",
                            type="circle",
                            children=[
                                dcc.Graph(
                                    id="article-network-like-graph",
                                    style={"width": "50%", "display": "none"},
                                    figure={
                                        "data": [],
                                        "layout": {
                                            "xaxis": {"visible": False},
                                            "yaxis": {"visible": False},
                                        },
                                    },
                                )
                            ],
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dcc.Loading(
                            id="loading-network-dislike-graph",
                            type="circle",
                            children=[
                                dcc.Graph(
                                    id="article-network-dislike-graph",
                                    style={"width": "50%", "display": "none"},
                                    figure={
                                        "data": [],
                                        "layout": {
                                            "xaxis": {"visible": False},
                                            "yaxis": {"visible": False},
                                        },
                                    },
                                )
                            ],
                        ),
                        width=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )

    @app.callback(
        [
            Output("keyword-freq", "children"),
            Output("keyword-freq", "style"),
            Output("keyword-agree", "children"),
            Output("keyword-agree", "style"),
            Output("keyword-disagree", "children"),
            Output("keyword-disagree", "style"),
        ],
        [Input("submit-button-keyword", "n_clicks")],
        [
            dash.dependencies.State("keyword-search", "value"),
            dash.dependencies.State("dropdown-collection", "value"),
        ],
    )
    def generate_keyword_mata_table(n_clicks, keyword_search, dropdown_collection):
        if n_clicks is None or not keyword_search:
            return (
                dash.no_update,
                {"display": "none"},
                dash.no_update,
                {"display": "none"},
                dash.no_update,
                {"display": "none"},
            )
        articles_relevant = extract_author_info_from_articles_title_having_keywords(
            target_collection=dropdown_collection,
            keyword=keyword_search,
            num_articles=NUM_ARTICLES,
        )
        if len(articles_relevant) > 0:
            all_commenters_descriptive_info = defaultdict(lambda: defaultdict(float))
            for article in articles_relevant:
                raw_commenters_info = (
                    extract_commenter_info_from_article_with_article_url(
                        target_collection=dropdown_collection, article_data=article
                    )
                )
                all_commenters_descriptive_info = summarize_commenters_metadata(
                    raw_commenters_info, all_commenters_descriptive_info
                )

            df = convert_commenters_metadata_to_dataframe(
                all_commenters_descriptive_info
            )
            top_freq_commenters = extract_top_freq_commenter_id(
                df, num_commenters=NUM_COMMENTERS
            )
            top_agree_commenters = extract_top_agree_commenter_id(
                df, num_commenters=NUM_COMMENTERS
            )
            top_disagree_commenters = extract_top_disagree_commenter_id(
                df, num_commenters=NUM_COMMENTERS
            )

            top_freq_commenters = ", ".join(
                [commenter for commenter in top_freq_commenters]
            )
            top_agree_commenters = ", ".join(
                [commenter for commenter in top_agree_commenters]
            )
            top_disagree_commenters = ", ".join(
                [commenter for commenter in top_disagree_commenters]
            )
            return (
                html.H6(f"留言次數最高的 {NUM_COMMENTERS} 位留言者: {top_freq_commenters}"),
                {"display": "block"},
                html.H6(f"推文次數最高的 {NUM_COMMENTERS} 位留言者: {top_agree_commenters}"),
                {"display": "block"},
                html.H6(f"噓文次數最高的 {NUM_COMMENTERS} 位留言者: {top_disagree_commenters}"),
                {"display": "block"},
            )
        return (
            html.H6(f""),
            {"display": "block"},
            html.H6(f"查無資料"),
            {"display": "block"},
            html.H6(f""),
            {"display": "block"},
        )

    @app.callback(
        [
            Output("article-network-like-graph", "figure"),
            Output("article-network-like-graph", "style"),
            Output("article-network-dislike-graph", "figure"),
            Output("article-network-dislike-graph", "style"),
        ],
        [Input("submit-button-keyword", "n_clicks")],
        [
            dash.dependencies.State("keyword-search", "value"),
            dash.dependencies.State("dropdown-collection", "value"),
        ],
    )
    def update_commenter_network_graph(n_clicks, keyword_search, dropdown_collection):
        if n_clicks is None:
            return (
                dash.no_update,
                {"width": "100%", "display": "none"},
                dash.no_update,
                {"width": "100%", "display": "none"},
            )
        temp_collection_id, board_name, keyword = preparation_network_graph(
            keyword=keyword_search, target_collection=dropdown_collection
        )
        data_like = generate_concurrency_network_data(
            temp_collection_id=temp_collection_id,
            comment_type="推",
            num_commenters=NUM_NETWORK_COMMENTERS,
        )
        data_dislike = generate_concurrency_network_data(
            temp_collection_id=temp_collection_id,
            comment_type="噓",
            num_commenters=NUM_NETWORK_COMMENTERS,
        )
        if len(data_like) > 0:
            like_graph = create_network_graph(
                concurrency_list=data_like,
                board_name=board_name,
                keyword=keyword,
                num_commenters=NUM_NETWORK_COMMENTERS,
                comment_type="推",
            )
            dislike_graph = create_network_graph(
                concurrency_list=data_dislike,
                board_name=board_name,
                keyword=keyword,
                num_commenters=NUM_NETWORK_COMMENTERS,
                comment_type="噓",
            )
        else:
            like_graph = keyword_no_result_figure()
            dislike_graph = keyword_no_result_figure()
        db[temp_collection_id].drop()

        return (
            like_graph,
            {"width": "100%", "display": "block"},
            dislike_graph,
            {"width": "100%", "display": "block"},
        )

    return app

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
            html.H1("PTT Comment Detector - Keyword", className="text-center mb-4"),
            html.Div(
                [
                    html.A(
                        dbc.Button(
                            "Go to Overview", outline=True, color="primary", className="mr-20", style={"color": "blue"}
                        ),
                        href="/overview",
                        style={"marginRight": "15px"}

                    ),
                    html.A(
                        dbc.Button(
                            "Go to Commenter", outline=True, color="secondary", className="ml-20", style={"color": "green"}
                        ),
                        href="/commenter"
                    ),
                ], style={"textAlign": "center"}
            ),
            html.Hr(),
            html.H5(
                f"Please enter the keywords and select the board you want to search.",
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
                                placeholder="Enter Keyword",
                            ),
                        ],
                        width=2,
                        className="mb-2 ml-4",
                        style={"marginRight": "10px"}

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
                        className="mb-2 mr-20"
                    ),
                    dbc.Col(
                        [
                            html.Button(
                                "Submit",
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
            html.H5(f"Some highly active commenters' account id", className="mb-3"),
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
                f"The concurrency (connection) between these accounts will be shown below",
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Loading(
                            id="loading-network-like-graph",
                            type="circle",
                            children=[dcc.Graph(id="article-network-like-graph",
                                                style={"width": "50%", "display": "none"},
                                                figure={
                                                    "data": [],
                                                    "layout": {"xaxis": {"visible": False}, "yaxis": {"visible": False}},
                                                }
                                                )],
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dcc.Loading(
                            id="loading-network-dislike-graph",
                            type="circle",
                            children=[dcc.Graph(id="article-network-dislike-graph",
                                                style = {"width": "50%", "display": "none"},
                                                figure = {
                                                    "data": [],
                                                    "layout": {"xaxis": {"visible": False}, "yaxis": {"visible": False}},
                                                }
                                                )],
                        ),
                        width=6,
                    ),
                ]
            ),
        ],
        fluid=True,
        className="my-4",
    )

    # app.layout = html.Div(
    # [
    #     html.H1("PTT Comment Detector - Keyword", style={"textAlign": "center"}),
    #     html.Hr(),
    #     html.H5(f"Please enter the keywords and select the board you want to search."),
    #     html.Div(
    #         children=[
    #             dcc.Input(
    #                 id="keyword-search",
    #                 type="text",
    #                 value="",
    #                 placeholder="Enter Keyword",
    #                 style={
    #                     "display": "inline-block",
    #                     "vertical-align": "middle",
    #                     "margin-right": "10px",
    #                 },
    #             ),
    #             dcc.Dropdown(
    #                 id="dropdown-collection",
    #                 options=[
    #                     {"label": "八卦版", "value": "gossip"},
    #                     {"label": "政黑版", "value": "politics"},
    #                 ],
    #                 value="gossip",
    #                 style={
    #                     "display": "inline-block",
    #                     "vertical-align": "middle",
    #                     "width": "150px",
    #                     "margin-right": "10px",
    #                 },
    #             ),
    #             html.Button(
    #                 "Submit",
    #                 id="submit-button-keyword",
    #                 disabled=False,
    #                 style={"display": "inline-block", "vertical-align": "middle"},
    #             ),
    #         ]
    #     ),
    #     html.Hr(),
    #     html.H5(f"Some highly active commenters' account id"),
    #     dcc.Loading(
    #         id="loading-keyword-info",
    #         type="circle",
    #         children=[
    #             html.Div(id="keyword-freq", style={"display": "none"}),
    #             html.Div(id="keyword-agree", style={"display": "none"}),
    #             html.Div(id="keyword-disagree", style={"display": "none"}),
    #         ],
    #     ),
    #     html.Hr(),
    #     html.H5(
    #         f"The concurrency (connection) between these accounts will be shown below"
    #     ),
    #     html.Div(
    #         children=[
    #             # html.H6(
    #             #     f"Concurrency Network Among Top {NUM_NETWORK_COMMENTERS} Commenters "
    #             #     f"Whose Commenters Show Liking in Related Article",
    #             # ),
    #             dcc.Loading(
    #                 id="loading-network-like-graph",
    #                 type="circle",
    #                 children=[
    #                     dcc.Graph(
    #                         id="article-network-like-graph",
    #                         style={"width": "75%", "display": "none"},
    #                     ),
    #                 ],
    #             ),
    #             # html.H6(
    #             #     f"Concurrency Network Among Top {NUM_NETWORK_COMMENTERS} Commenters "
    #             #     f"Whose Commenters Show Dis-liking in Related Article",
    #             # ),
    #             dcc.Loading(
    #                 id="loading-network-dislike-graph",
    #                 type="circle",
    #                 children=[
    #                     dcc.Graph(
    #                         id="article-network-dislike-graph",
    #                         style={"width": "75%", "display": "none"},
    #                     ),
    #                 ],
    #             ),
    #         ]
    #     ),
    # ]
    # )


    @app.callback(
        [
            Output("keyword-freq", "children"),
            Output("keyword-freq", "style"),
            Output("keyword-agree", "children"),
            Output("keyword-agree", "style"),
            Output("keyword-disagree", "children"),
            Output("keyword-disagree", "style"),
            Output("submit-button-keyword", "disabled"),
        ],
        [Input("submit-button-keyword", "n_clicks")],
        [
            dash.dependencies.State("keyword-search", "value"),
            dash.dependencies.State("dropdown-collection", "value"),
        ],
    )
    def generate_keyword_mata_table(n_clicks, keyword_search, dropdown_collection):
        disabled_status = True
        if n_clicks is None or not keyword_search:
            disabled_status = False
            return (
                dash.no_update,
                {"display": "none"},
                dash.no_update,
                {"display": "none"},
                dash.no_update,
                {"display": "none"},
                disabled_status,
            )
        articles_relevant = extract_author_info_from_articles_title_having_keywords(
            target_collection=dropdown_collection,
            keyword=keyword_search,
            num_articles=NUM_ARTICLES,
        )
        all_commenters_descriptive_info = defaultdict(lambda: defaultdict(float))
        for article in articles_relevant:
            raw_commenters_info = extract_commenter_info_from_article_with_article_url(
                target_collection=dropdown_collection, article_data=article
            )
            all_commenters_descriptive_info = summarize_commenters_metadata(
                raw_commenters_info, all_commenters_descriptive_info
            )

        df = convert_commenters_metadata_to_dataframe(all_commenters_descriptive_info)
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
        disabled_status = False
        return (
            html.H6(f"留言次數最高的 {NUM_COMMENTERS} 位留言者: {top_freq_commenters}"),
            {"display": "block"},
            html.H6(f"推文次數最高的 {NUM_COMMENTERS} 位留言者: {top_agree_commenters}"),
            {"display": "block"},
            html.H6(f"噓文次數最高的 {NUM_COMMENTERS} 位留言者: {top_disagree_commenters}"),
            {"display": "block"},
            disabled_status,
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
        if n_clicks is None or not keyword_search:
            return (
                dash.no_update, {"width": "100%", "display": "none"},
                dash.no_update, {"width": "100%", "display": "none"}
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
        db[temp_collection_id].drop()

        return (
            like_graph,
            {"width": "100%", "display": "block"},
            dislike_graph,
            {"width": "100%", "display": "block"},
        )

    return app

import dash
import jieba.analyse
from dotenv import load_dotenv
from flask_caching import Cache
from dash import dcc, html, Input, Output
from collections import defaultdict
from utils_dashboard.plot_generate_wordcloud import wordcloud_graph
from utils_dashboard.plot_generate_network_2D import draw_network_2d
from utils_dashboard.plot_generate_heatmap import heatmap_commenter_activities
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
NUM_ARTICLES = 200
NUM_COMMENTERS = 5

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]


def create_detail_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
    app = dash.Dash(
        __name__,
        requests_pathname_prefix=requests_pathname_prefix,
        external_stylesheets=external_stylesheets,
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

    app.layout = html.Div(
        [
            html.H1("PTT Comment Detector", style={"textAlign": "center"}),
            html.Hr(),
            html.Div(
                children=[
                    dcc.Input(
                        id="keyword-search",
                        type="text",
                        value="",
                        placeholder="Enter Keyword",
                        style={
                            "display": "inline-block",
                            "vertical-align": "middle",
                            "margin-right": "10px",
                        },
                    ),
                    dcc.Dropdown(
                        id="dropdown-collection",
                        options=[
                            {"label": "八卦版", "value": "gossip"},
                            {"label": "政黑版", "value": "politics"},
                        ],
                        value="gossip",
                        style={
                            "display": "inline-block",
                            "vertical-align": "middle",
                            "width": "150px",
                            "margin-right": "10px",
                        },
                    ),
                    html.Button(
                        "Submit",
                        id="submit-button-keyword",
                        style={"display": "inline-block", "vertical-align": "middle"},
                    ),
                ]
            ),
            html.Div(id="keyword-freq", style={"display": "none"}),
            html.Div(id="keyword-agree", style={"display": "none"}),
            html.Div(id="keyword-disagree", style={"display": "none"}),
            dcc.Graph(id="article-network-graph", style={"display": "none"}),
            # html.Div(style={"display": "flex", "width": "100%"},
            #          children=[
            #              html.H3("Top 5 commenters id"),
            #              dash_table.DataTable(id="table-keyword-data",
            #                                   style_table={"width": "100%"},
            #                                   style_cell = {"height": "auto",
            #                                                  "width": "150px",
            #                                                  "minWidth": "15px",
            #                                                  "maxWidth": "180px",
            #                                                  "whiteSpace": "normal"},
            #                                   style_header = {"textAlign": "center"},
            #
            #                                   )
            #          ]),
            html.Div(id="table-keyword", style={"display": "none"}),
            html.Br(),
            html.Br(),
            html.Div(
                children=[
                    dcc.Input(
                        id="account-id",
                        type="text",
                        value="",
                        placeholder="Enter Account ID",
                        style={
                            "display": "inline-block",
                            "vertical-align": "middle",
                            "margin-right": "10px",
                        },
                    ),
                    html.Button(
                        "Submit",
                        id="submit-button-id",
                        style={"display": "inline-block", "vertical-align": "middle"},
                    ),
                ]
            ),
            html.Div(id="graph-data", style={"display": "none"}),

            html.Div(
                children=[
                    dcc.Graph(
                        id="activity-graph", style={"width": "49%", "display": "none"}
                    ),
                    html.Img(
                        id="wordcloud-graph", style={"width": "49%", "display": "none"}
                    ),
                ]
            ),
        ]
    )

    @app.callback(
        [Output("wordcloud-graph", "src"), Output("wordcloud-graph", "style")],
        [Input("submit-button-id", "n_clicks")],
        [dash.dependencies.State("account-id", "value")],
    )
    def generate_wordcloud_graph(n_clicks, account_id):
        if n_clicks is None or not account_id:
            return dash.no_update, {"display": "none"}

        fig = wordcloud_graph(account_id=account_id)
        return fig, {"width": "49%", "display": "inline-block"}

    @app.callback(
        [Output("activity-graph", "figure"), Output("activity-graph", "style")],
        [Input("submit-button-id", "n_clicks")],
        [dash.dependencies.State("account-id", "value")],
    )
    def generate_heatmap_commenter_activities(n_clicks, account_id: str):
        if n_clicks is None or not account_id:
            return dash.no_update, {"display": "none"}

        fig = heatmap_commenter_activities(account_id=account_id)
        return fig, {"width": "49%", "display": "inline-block"}

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
        return (
            f"留言次數最高的 {NUM_COMMENTERS} 位留言者: {top_freq_commenters}",
            {"display": "block"},
            f"推文次數最高的 {NUM_COMMENTERS} 位留言者: {top_agree_commenters}",
            {"display": "block"},
            f"噓文次數最高的 {NUM_COMMENTERS} 位留言者: {top_disagree_commenters}",
            {"display": "block"},
        )
    # @app.callback(
    #     [
    #         Output("article-network-graph", "figure"),
    #         Output("article-network-graph", "style")
    #     ],
    #     [Input("submit-button-keyword", "n_clicks")],
    #     [dash.dependencies.State("keyword-search", "value")],
    # )
    # def generate_article_network_2d_graph(raw_article_info):
    #     organized_authors_info = [
    #         (
    #             author["article_data"]["author"],
    #             author["article_data"]["ipaddress"],
    #             author["article_url"],
    #             "author",
    #         )
    #         for author in raw_article_info
    #     ]
    #     return draw_network_2d(article_author_data=organized_authors_info,
    #                            keyword=)
    return app

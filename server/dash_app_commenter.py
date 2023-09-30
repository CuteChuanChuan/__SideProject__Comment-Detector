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


def create_commenter_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
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
            html.H1("PTT Comment Detector - Commenter", style={"textAlign": "center"}),
            html.Hr(),
            html.H5(f"Please enter the commenter account id you want to search. "
                    f"We will show some information about that account id"),
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
            html.Br(),
            html.Hr(),
            html.Div(
                children=[
                    html.H6("Activity Graph (Area circled by red line is the working hours)",
                            style={"display": "inline-block", "width": "49%"}),
                    dcc.Loading(
                        id="loading-account-activity-graph",
                        type="circle",
                        children=[
                            dcc.Graph(id="activity-graph", style={"width": "49%", "display": "none"}),
                        ],
                    ),
                    html.Br(),
                    html.H6("Wordcloud Graph (Please wait since the system will analyze all comments of that account)",
                            style={"display": "inline-block", "width": "49%"}),
                    dcc.Loading(
                        id="loading-account-wordcloud-graph",
                        type="circle",
                        children=[
                            html.Img(id="wordcloud-graph", style={"width": "49%", "display": "none"}),
                        ],
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

    return app

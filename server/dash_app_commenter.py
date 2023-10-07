import dash
import jieba.analyse
from dotenv import load_dotenv
from flask_caching import Cache
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
from utils_dashboard.plot_generate_wordcloud import wordcloud_graph
from utils_dashboard.plot_generate_heatmap import heatmap_commenter_activities


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
            html.H1("PTT Comment Detector - 留言者分析", className="text-center mb-4"),
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
                            className="ml-20",
                            style={"color": "gray"},
                        ),
                        href="/keyword",
                        style={"marginRight": "15px"},
                    ),
                    html.A(
                        dbc.Button(
                            "留言者分析",
                            outline=True,
                            color="primary",
                            className="ml-20",
                            style={"color": "black", "font-weight": "bold"},
                        ),
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
            html.H5(f"留言者帳號搜尋", style={"font-weight": "bold"}),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Input(
                                id="account-id",
                                type="text",
                                value="",
                                placeholder="請輸入留言者帳號",
                                className="mr-10",
                            ),
                            html.Button(
                                "確認",
                                id="submit-button-id",
                            ),
                        ],
                        width=6,
                        className="mb-4 ml-2",
                    ),
                ]
            ),
            html.H6(f"此留言者在八卦版 & 政黑版的行為", style={"font-weight": "bold"}),
            dbc.Row(
                [
                    dbc.Col(
                        html.H6("留言時段熱度圖 (紅色框選區域為上班時段)"),
                        width=6,
                    ),
                    dbc.Col(
                        html.H6("留言文字雲 (運算時間依留言數量而有所變化，請稍候)"),
                        width=6,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Loading(
                            id="loading-account-activity-graph",
                            type="circle",
                            children=[
                                dcc.Graph(
                                    id="activity-graph",
                                    style={"width": "100%", "display": "none"},
                                ),
                            ],
                        ),
                        width=6,
                    ),
                    dbc.Col(
                        dcc.Loading(
                            id="loading-account-wordcloud-graph",
                            type="circle",
                            children=[
                                html.Img(
                                    id="wordcloud-graph",
                                    style={"width": "100%", "display": "none"},
                                ),
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
        [Output("wordcloud-graph", "src"), Output("wordcloud-graph", "style")],
        [Input("submit-button-id", "n_clicks")],
        [dash.dependencies.State("account-id", "value")],
    )
    def generate_wordcloud_graph(n_clicks, account_id):
        if n_clicks is None or not account_id:
            return dash.no_update, {"display": "none"}

        fig = wordcloud_graph(account_id=account_id)
        return fig, {"width": "100%", "display": "block"}

    @app.callback(
        [Output("activity-graph", "figure"), Output("activity-graph", "style")],
        [Input("submit-button-id", "n_clicks")],
        [dash.dependencies.State("account-id", "value")],
    )
    def generate_heatmap_commenter_activities(n_clicks, account_id: str):
        if n_clicks is None or not account_id:
            return dash.no_update, {"display": "none"}

        fig = heatmap_commenter_activities(account_id=account_id)
        return fig, {"width": "100%", "display": "block"}

    return app

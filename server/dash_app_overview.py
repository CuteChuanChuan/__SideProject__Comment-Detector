import dash
import jieba.analyse
from dash import dash_table
from dotenv import load_dotenv
from flask_caching import Cache
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from utils_dashboard.func_update_crawling_data import update_layout
from utils_dashboard.func_retrieve_top_n_breaking_news import update_breaking_news
from utils_dashboard.func_retrieve_top_n_popular_news import update_popular_news
from utils_dashboard.plot_generate_barchart_keywords import generate_barchart_keywords

load_dotenv(verbose=True)

DICT_FILE = "utils_dashboard/tc_dict.txt"
STOP_FILE = "utils_dashboard/stopwords.txt"
TC_FONT_PATH = "utils_dashboard/NotoSerifTC-Regular.otf"

jieba.set_dictionary(DICT_FILE)
jieba.analyse.set_stop_words(STOP_FILE)

NUM_NEWS = 10
TIMEOUT = 60

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]


def create_overview_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
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
            html.H1("PTT Comment Detector - Overview", className="text-center mb-4"),
            html.Div(
                [
                    html.A(
                        dbc.Button(
                            "Go to Keyword",
                            outline=True,
                            color="primary",
                            className="mr-20",
                            style={"color": "blue"},
                        ),
                        href="/keyword",
                        style={"marginRight": "15px"},
                    ),
                    html.A(
                        dbc.Button(
                            "Go to Commenter",
                            outline=True,
                            color="secondary",
                            className="ml-20",
                            style={"color": "green"},
                        ),
                        href="/commenter",
                    ),
                ],
                style={"textAlign": "center"},
            ),
            html.Hr(),
            dbc.Row([dbc.Col(html.H3("Overview of Article, Comments, Accounts Collected", className="mb-4 pl-8 pr-8"))]),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Loading(
                            id="loading-overview-info",
                            type="circle",
                            children=[
                                dcc.Interval(id="interval-component", interval=20 * 1000, n_intervals=0),
                                html.Div(id="live-update-text"),
                            ],
                        ),
                        width=12,
                    )
                ],
                className="mb-4 pl-8 pr-8"
            ),
            html.Hr(),
            dbc.Row([dbc.Col(html.H3("Keywords of 2 Boards (Gossiping and Politics)"))]),
            dbc.Row([dbc.Col(dcc.Dropdown(
                id="dropdown",
                options=[
                    {"label": "昨天", "value": 1},
                    {"label": "過去三天", "value": 3},
                    {"label": "過去一週", "value": 7},
                ],
                value=1,
            ), width=6)]),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="gossips-title-keyword-barchart", style={"width": "100%"}), className="col-md-3"),
                    dbc.Col(dcc.Graph(id="gossips-comments-keyword-barchart", style={"width": "100%"}), className="col-md-3"),
                    dbc.Col(dcc.Graph(id="politic-title-keyword-barchart", style={"width": "100%"}), className="col-md-3"),
                    dbc.Col(dcc.Graph(id="politic-comments-keyword-barchart", style={"width": "100%"}), className="col-md-3"),
                ],
                className="mb-4 pl-8 pr-8"
            ),
            html.Hr(),
            dbc.Row([dbc.Col(html.H3(f"The Top 10 Breaking and Popular Articles in the Gossiping Board"),
                             className="mb-4 pl-8 pr-8")]),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5(f"[八卦版] 爆卦類文章 - 留言數量前 {NUM_NEWS} 名"),
                            dash_table.DataTable(
                                id="gossips-news-breaking",
                                style_table={"width": "100%"},
                                style_cell={
                                    "height": "auto",
                                    "width": "150px",
                                    "minWidth": "15px",
                                    "maxWidth": "180px",
                                    "whiteSpace": "normal",
                                },
                                style_header={"textAlign": "center"},
                                style_cell_conditional=[
                                    {
                                        "if": {"column_id": "文章標題"},
                                        "width": "400px",
                                        "textAlign": "left",
                                        "height": "auto",
                                    },
                                    {
                                        "if": {"column_id": "作者"},
                                        "width": "110px",
                                        "textAlign": "left",
                                        "height": "auto",
                                    },
                                    {
                                        "if": {"column_id": "留言數"},
                                        "width": "15px",
                                        "textAlign": "right",
                                        "height": "auto",
                                    },
                                    {
                                        "if": {"column_id": "文章連結"},
                                        "width": "350px",
                                        "textAlign": "left",
                                        "font_size": "12px",
                                        "height": "auto",
                                    },
                                ],
                                columns=[
                                    {"name": i, "id": i, "presentation": "markdown"}
                                    for i in update_breaking_news("gossip").columns
                                ],
                                markdown_options={"html": True},
                                data=None,
                            ),
                            dcc.Interval(
                                id="interval-component-table-breaking",
                                interval=240 * 1000,
                                n_intervals=0,
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.H5(f"[八卦版] 爆文文章 (推 - 噓 >= 100) - 留言數量前 {NUM_NEWS} 名"),
                            dash_table.DataTable(
                                id="gossips-news-popular",
                                style_table={"width": "100%"},
                                style_cell={
                                    "height": "auto",
                                    "width": "150px",
                                    "minWidth": "15px",
                                    "maxWidth": "180px",
                                    "whiteSpace": "normal",
                                },
                                style_header={"textAlign": "center"},
                                style_cell_conditional=[
                                    {
                                        "if": {"column_id": "文章標題"},
                                        "width": "400px",
                                        "textAlign": "left",
                                        "height": "auto",
                                    },
                                    {
                                        "if": {"column_id": "作者"},
                                        "width": "110px",
                                        "textAlign": "left",
                                        "height": "auto",
                                    },
                                    {
                                        "if": {"column_id": "留言數"},
                                        "width": "15px",
                                        "textAlign": "right",
                                        "height": "auto",
                                    },
                                    {
                                        "if": {"column_id": "文章連結"},
                                        "width": "350px",
                                        "textAlign": "left",
                                        "font_size": "12px",
                                        "height": "auto",
                                    },
                                ],
                                columns=[
                                    {"name": i, "id": i, "presentation": "markdown"}
                                    for i in update_popular_news("gossip").columns
                                ],
                                markdown_options={"html": True},
                                data=None,
                            ),
                            dcc.Interval(
                                id="interval-component-table-popular",
                                interval=240 * 1000,
                                n_intervals=0,
                            ),
                        ],
                        width=6,
                    )
                ]
            )
        ],
        fluid=True,
    )

    # app.layout = html.Div(
    #     [
    #         html.H1("PTT Comment Detector - Overview", style={"textAlign": "center"}),
    #         html.Hr(),
    #         html.H3(f"Overview of Article, Comments, Accounts Collected"),
    #         dcc.Loading(
    #             id="loading-overview-info",
    #             type="circle",
    #             children=[
    #                 dcc.Interval(
    #                     id="interval-component", interval=20 * 1000, n_intervals=0
    #                 ),
    #                 html.Div(id="live-update-text"),
    #             ],
    #         ),
    #         html.Br(),
    #         html.Hr(),
    #         html.H3(f"Keywords of 2 Boards (Gossiping and Politics)"),
    #         dcc.Dropdown(
    #             id="dropdown",
    #             options=[
    #                 {"label": "昨天", "value": 1},
    #                 {"label": "過去三天", "value": 3},
    #                 {"label": "過去一週", "value": 7},
    #             ],
    #             value=1,
    #         ),
    #         dcc.Loading(
    #             id="loading-keyword-overview-info",
    #             type="circle",
    #             children=[
    #                 html.Div(
    #                     children=[
    #                         dcc.Graph(
    #                             id="gossips-title-keyword-barchart",
    #                             style={"width": "25%", "display": "none"},
    #                         ),
    #                         dcc.Graph(
    #                             id="gossips-comments-keyword-barchart",
    #                             style={"width": "25%", "display": "none"},
    #                         ),
    #                         dcc.Graph(
    #                             id="politic-title-keyword-barchart",
    #                             style={"width": "25%", "display": "none"},
    #                         ),
    #                         dcc.Graph(
    #                             id="politic-comments-keyword-barchart",
    #                             style={"width": "25%", "display": "none"},
    #                         ),
    #                     ]
    #                 ),
    #             ],
    #         ),
    #         html.Hr(),
    #         html.H3(f"The Top 10 Breaking and Popular Articles in the Gossiping Board"),
    #         html.Div(
    #             style={"display": "flex", "width": "100%"},
    #             children=[
    #                 html.Div(
    #                     style={"width": "49.5%", "marginRight": "1%"},
    #                     children=[
    #                         html.H5(f"[八卦版] 爆卦類文章 - 留言數量前 {NUM_NEWS} 名"),
    #                         dash_table.DataTable(
    #                             id="gossips-news-breaking",
    #                             style_table={"width": "100%"},
    #                             style_cell={
    #                                 "height": "auto",
    #                                 "width": "150px",
    #                                 "minWidth": "15px",
    #                                 "maxWidth": "180px",
    #                                 "whiteSpace": "normal",
    #                             },
    #                             style_header={"textAlign": "center"},
    #                             style_cell_conditional=[
    #                                 {
    #                                     "if": {"column_id": "文章標題"},
    #                                     "width": "400px",
    #                                     "textAlign": "left",
    #                                     "height": "auto",
    #                                 },
    #                                 {
    #                                     "if": {"column_id": "作者"},
    #                                     "width": "110px",
    #                                     "textAlign": "left",
    #                                     "height": "auto",
    #                                 },
    #                                 {
    #                                     "if": {"column_id": "留言數"},
    #                                     "width": "15px",
    #                                     "textAlign": "right",
    #                                     "height": "auto",
    #                                 },
    #                                 {
    #                                     "if": {"column_id": "文章連結"},
    #                                     "width": "350px",
    #                                     "textAlign": "left",
    #                                     "font_size": "12px",
    #                                     "height": "auto",
    #                                 },
    #                             ],
    #                             columns=[
    #                                 {"name": i, "id": i, "presentation": "markdown"}
    #                                 for i in update_breaking_news("gossip").columns
    #                             ],
    #                             markdown_options={"html": True},
    #                             data=None,
    #                         ),
    #                         dcc.Interval(
    #                             id="interval-component-table-breaking",
    #                             interval=240 * 1000,
    #                             n_intervals=0,
    #                         ),
    #                     ],
    #                 ),
    #                 html.Div(
    #                     style={"width": "49.5%"},
    #                     children=[
    #                         html.H5(f"[八卦版] 爆文文章 (推 - 噓 >= 100) - 留言數量前 {NUM_NEWS} 名"),
    #                         dash_table.DataTable(
    #                             id="gossips-news-popular",
    #                             style_table={"width": "100%"},
    #                             style_cell={
    #                                 "height": "auto",
    #                                 "width": "150px",
    #                                 "minWidth": "15px",
    #                                 "maxWidth": "180px",
    #                                 "whiteSpace": "normal",
    #                             },
    #                             style_header={"textAlign": "center"},
    #                             style_cell_conditional=[
    #                                 {
    #                                     "if": {"column_id": "文章標題"},
    #                                     "width": "400px",
    #                                     "textAlign": "left",
    #                                     "height": "auto",
    #                                 },
    #                                 {
    #                                     "if": {"column_id": "作者"},
    #                                     "width": "110px",
    #                                     "textAlign": "left",
    #                                     "height": "auto",
    #                                 },
    #                                 {
    #                                     "if": {"column_id": "留言數"},
    #                                     "width": "15px",
    #                                     "textAlign": "right",
    #                                     "height": "auto",
    #                                 },
    #                                 {
    #                                     "if": {"column_id": "文章連結"},
    #                                     "width": "350px",
    #                                     "textAlign": "left",
    #                                     "font_size": "12px",
    #                                     "height": "auto",
    #                                 },
    #                             ],
    #                             columns=[
    #                                 {"name": i, "id": i, "presentation": "markdown"}
    #                                 for i in update_popular_news("gossip").columns
    #                             ],
    #                             markdown_options={"html": True},
    #                             data=None,
    #                         ),
    #                         dcc.Interval(
    #                             id="interval-component-table-popular",
    #                             interval=240 * 1000,
    #                             n_intervals=0,
    #                         ),
    #                     ],
    #                 ),
    #             ],
    #         ),
    #     ]
    # )

    @app.callback(
        Output("live-update-text", "children"),
        [Input("interval-component", "n_intervals")],
    )
    @cache.memoize(timeout=TIMEOUT)
    def update_crawling_data(n_intervals):
        updated_info = update_layout()
        return updated_info

    @app.callback(
        [
            Output("gossips-title-keyword-barchart", "figure"),
            Output("gossips-comments-keyword-barchart", "figure"),
            Output("politic-title-keyword-barchart", "figure"),
            Output("politic-comments-keyword-barchart", "figure"),

        ],
        [Input("dropdown", "value")],
    )
    @cache.memoize(timeout=24 * 60 * 60)
    def generate_barchart_keywords_for_boards(selected_value):
        gossips_title_data = generate_barchart_keywords(
            target_collection="gossip", n_days=selected_value, source="標題"
        )
        gossips_comments_data = generate_barchart_keywords(
            target_collection="gossip", n_days=selected_value, source="留言"
        )
        politic_title_data = generate_barchart_keywords(
            target_collection="politics", n_days=selected_value, source="標題"
        )
        politic_comments_data = generate_barchart_keywords(
            target_collection="politics", n_days=selected_value, source="留言"
        )
        return (
            gossips_title_data,
            gossips_comments_data,
            politic_title_data,
            politic_comments_data
        )

    @app.callback(
        Output("gossips-news-breaking", "data"),
        [Input("interval-component-table-breaking", "n_intervals")],
    )
    @cache.memoize(timeout=TIMEOUT * 20)
    def update_gossips_news_breaking(n_intervals):
        return update_breaking_news(ptt_board="gossip", num_news=NUM_NEWS).to_dict(
            "records"
        )

    @app.callback(
        Output("gossips-news-popular", "data"),
        [Input("interval-component-table-popular", "n_intervals")],
    )
    @cache.memoize(timeout=TIMEOUT * 20)
    def update_gossips_news_popular(n_intervals):
        return update_popular_news(ptt_board="gossip", num_news=NUM_NEWS).to_dict(
            "records"
        )

    return app

import dash
import jieba.analyse
from dash import dash_table
from dotenv import load_dotenv
from flask_caching import Cache
from dash import dcc, html, Input, Output
from utils_dashboard.func_update_crawling_data import update_layout
from utils_dashboard.plot_generate_wordcloud import wordcloud_graph
from utils_dashboard.plot_generate_heatmap import heatmap_commenter_activities
from utils_dashboard.func_retrieve_top_n_breaking_news import update_breaking_news
from utils_dashboard.config_dashboard import neo4j_url, neo4j_user, neo4j_password
from utils_dashboard.plot_generate_barchart_keywords import generate_barchart_keywords
from utils_dashboard.plot_generate_network_graph_one_account import network_graph_one_account

load_dotenv(verbose=True)

DICT_FILE = "utils_dashboard/tc_dict.txt"
STOP_FILE = "utils_dashboard/stopwords.txt"
TC_FONT_PATH = "utils_dashboard/NotoSerifTC-Regular.otf"

jieba.set_dictionary(DICT_FILE)
jieba.analyse.set_stop_words(STOP_FILE)

NUM_NEWS = 10
TIMEOUT = 40

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]


def create_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
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
                    dcc.Interval(
                        id="interval-component", interval=3 * 1000, n_intervals=0
                    ),
                    html.Div(id="live-update-text"),
                ]
            ),
            dcc.Dropdown(
                id="dropdown",
                options=[{"label": "昨天", "value": 1},
                         {"label": "過去三天", "value": 3},
                         {"label": "過去一週", "value": 7}],
                value=1,
            ),
            html.Div(children=[
                dcc.Graph(id="gossips-title-keyword-barchart", style={"width": "25%", "display": "none"}),
                dcc.Graph(id="gossips-comments-keyword-barchart", style={"width": "25%", "display": "none"}),
                dcc.Graph(id="politic-title-keyword-barchart", style={"width": "25%", "display": "none"}),
                dcc.Graph(id="politic-comments-keyword-barchart", style={"width": "25%", "display": "none"})
            ]),
            html.Hr(),
            html.Div(
                children=[
                    html.H3(f"八卦版爆卦文章 - 留言數量前 {NUM_NEWS} 名"),
                    dash_table.DataTable(
                        id="gossips-news",
                        style_table={"width": "1025px"},
                        style_cell={
                            "height": "auto",
                            "width": "150px",
                            "minWidth": "30px",
                            "maxWidth": "180px",
                            "whiteSpace": "normal",
                        },
                        style_header={"textAlign": "center"},
                        style_cell_conditional=[
                            {
                                "if": {"column_id": "文章標題"},
                                "width": "500px",
                                "textAlign": "left",
                                "height": "auto",
                            },
                            {
                                "if": {"column_id": "留言數"},
                                "width": "30px",
                                "textAlign": "right",
                                "height": "auto",
                            },
                            {
                                "if": {"column_id": "文章連結"},
                                "width": "500px",
                                "textAlign": "left",
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
                    # dash_table.DataTable(id="politic-news",
                    #                      style_cell={'textAlign': 'left', 'width': '49%', 'height': 'auto',
                    #                                  'minWidth': '180px', 'maxWidth': '180px',
                    #                                  'whiteSpace': 'normal'
                    #                                  },
                    #                      columns=[{"name": i, "id": i} for i in update_breaking_news("politics").columns],
                    #                      data=None),
                    dcc.Interval(
                        id="interval-component-table", interval=20 * 1000, n_intervals=0
                    ),
                ]
            ),
            html.Br(),
            dcc.Input(
                id="account-id", type="text", value="", placeholder="Enter Account ID"
            ),
            html.Button("Submit", id="submit-button-id"),
            html.Div(id="graph-data", style={"display": "none"}),
            dcc.Graph(id="network-graph", style={"display": "none"}),
            html.Div(
                children=[
                    html.Img(
                        id="wordcloud-graph", style={"width": "49%", "display": "none"}
                    ),
                    dcc.Graph(
                        id="activity-graph", style={"width": "49%", "display": "none"}
                    ),
                ]
            ),
        ]
    )

    @app.callback(
        Output("live-update-text", "children"),
        [Input("interval-component", "n_intervals")],
    )
    @cache.memoize(timeout=TIMEOUT)
    def update_crawling_data(n_intervals):
        updated_info = update_layout()
        return updated_info

    @app.callback([Output("gossips-title-keyword-barchart", "figure"),
                   Output("gossips-title-keyword-barchart", "style"),
                   Output("gossips-comments-keyword-barchart", "figure"),
                   Output("gossips-comments-keyword-barchart", "style"),
                   Output("politic-title-keyword-barchart", "figure"),
                   Output("politic-title-keyword-barchart", "style"),
                   Output("politic-comments-keyword-barchart", "figure"),
                   Output("politic-comments-keyword-barchart", "style")
                   ],
                  [Input('dropdown', 'value')])
    @cache.memoize(timeout=24*60*60)
    def generate_barchart_keywords_for_boards(selected_value):
        gossips_title_data = generate_barchart_keywords(target_collection="gossip", n_days=selected_value, source="標題")
        gossips_comments_data = generate_barchart_keywords(target_collection="gossip", n_days=selected_value, source="留言")
        politic_title_data = generate_barchart_keywords(target_collection="politics", n_days=selected_value, source="標題")
        politic_comments_data = generate_barchart_keywords(target_collection="politics", n_days=selected_value, source="留言")
        return (gossips_title_data, {"width": "25%", "display": "inline-block"},
                gossips_comments_data, {"width": "25%", "display": "inline-block"},
                politic_title_data, {"width": "25%", "display": "inline-block"},
                politic_comments_data, {"width": "25%", "display": "inline-block"})

    @app.callback(
        Output("gossips-news", "data"),
        [Input("interval-component-table", "n_intervals")],
    )
    @cache.memoize(timeout=TIMEOUT)
    def update_gossips_news(n_intervals):
        return update_breaking_news(ptt_board="gossip", num_news=NUM_NEWS).to_dict(
            "records"
        )

    @app.callback(
        [Output("network-graph", "figure"), Output("network-graph", "style")],
        [Input("submit-button-id", "n_clicks")],
        [dash.dependencies.State("account-id", "value")],
    )
    def generate_network_graph_one_account(n_clicks, account_id):
        if n_clicks is None or not account_id:
            return dash.no_update, {"display": "none"}

        fig = network_graph_one_account(account_id=account_id)
        return fig, {"display": "block"}

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

    # @app.callback(
    #     Output('neovis-container', 'children'),
    #     Input('interval-component', 'n_intervals')
    # )
    # def update_graph(n_intervals):
    #     return html.Div([
    #         html.Div(id="viz", style={"width": "800px", "height": "600px"}),
    #         html.Script(src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"),
    #         html.Script(src="https://cdn.jsdelivr.net/npm/neovis.js@1.5.0/dist/neovis.js"),
    #         html.Script(neovis_script)
    #     ])

    return app

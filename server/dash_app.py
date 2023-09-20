import os
import dash
import jieba
import jieba.analyse
import networkx as nx
from py2neo import Graph
from dotenv import load_dotenv
from wordcloud import WordCloud
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
from pymongo.mongo_client import MongoClient
from data_processing.aggregate_mongo import count_articles, count_comments, count_accounts

load_dotenv(verbose=True)

uri = os.getenv("ATLAS_URI", "None")
client = MongoClient(uri)
db = client[os.getenv("ATLAS_DATABASE", "ptt")]
DICT_FILE = "tc_dict.txt"
STOP_FILE = "stopwords.txt"
TC_FONT_PATH = "NotoSerifTC-Regular.otf"

jieba.set_dictionary(DICT_FILE)
jieba.analyse.set_stop_words(STOP_FILE)


def create_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
    graph = Graph(uri=f"{os.getenv('NEO4J_URL')}:7687",
                  auth=(os.getenv("NEO4J_USERNAME", "YourAccount"), os.getenv("NEO4J_PASSWORD", "YourPassword")))

    app = dash.Dash(__name__, requests_pathname_prefix=requests_pathname_prefix)
    app.scripts.config.serve_locally = True
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    app.layout = html.Div([
        dcc.Interval(
            id='interval-component',
            interval=3*1000,  # in milliseconds
            n_intervals=0
        ),
        html.H1('PTT Comment Detector', style={'textAlign': 'center'}),
        html.Div(id='live-update-text'),
        dcc.Input(id='account-id', type='text', value='', placeholder='Enter Account ID'),
        html.Button('Submit', id='submit-button'),
        html.Div(id='graph-data', style={'display': 'none'}),
        dcc.Graph(id='network-graph', style={'display': 'none'}),
        html.Img(id='wordcloud-graph', style={'display': 'none'})
    ])

    @app.callback(
        Output('live-update-text', 'children'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_layout(n_intervals):
        total_articles = count_articles("gossip") + count_articles("politics")
        total_comments = count_comments("gossip") + count_comments("politics")
        total_accounts = count_accounts("gossip") + count_accounts("politics")

        return [
            html.Div([
                html.H4('Crawled Article Count', style={'textAlign': 'center'}),
                html.H1(f'{total_articles}', style={'textAlign': 'center'}),
                html.H5('Articles', style={'textAlign': 'center'})
            ], style={'width': '33%', 'display': 'inline-block'}),

            html.Div([
                html.H4('Crawled Comment Count', style={'textAlign': 'center'}),
                html.H1(f'{total_comments}', style={'textAlign': 'center'}),
                html.H5('Comments', style={'textAlign': 'center'})
            ], style={'width': '33%', 'display': 'inline-block'}),

            html.Div([
                html.H4('Crawled Account Count', style={'textAlign': 'center'}),
                html.H1(f'{total_accounts}', style={'textAlign': 'center'}),
                html.H5('Accounts', style={'textAlign': 'center'})
            ], style={'width': '33%', 'display': 'inline-block'}),
        ]


    @app.callback(
        [Output('network-graph', 'figure'),
         Output('network-graph', 'style')],
        [Input('submit-button', 'n_clicks')],
        [dash.dependencies.State('account-id', 'value')]
    )
    def load_graph(n_clicks, account_id):
        if n_clicks is None or not account_id:
            return dash.no_update, {'display': 'none'}

        query = (f"MATCH (a1:Article {{article: 'https://www.ptt.cc/bbs/Gossiping/M.1694741448.A.CCB.html'}}) "
                 f"MATCH (commenter:Commenter_id)-[:RESPONDS]->(a1) "
                 f"WHERE commenter.id = '{account_id}' "
                 f"WITH commenter, a1 "
                 f"MATCH (a2:Article {{article: 'https://www.ptt.cc/bbs/Gossiping/M.1694956794.A.F1A.html'}}) "
                 f"MATCH (commenter)-[:RESPONDS]->(a2) "
                 f"MATCH (a3:Article {{article: 'https://www.ptt.cc/bbs/Gossiping/M.1694952559.A.90D.html'}}) "
                 f"MATCH (commenter)-[:RESPONDS]->(a3) "
                 f"MATCH (a4:Article {{article: 'https://www.ptt.cc/bbs/Gossiping/M.1694846678.A.101.html'}}) "
                 f"MATCH (commenter)-[:RESPONDS]->(a4) "
                 f"MATCH (a5:Article {{article: 'https://www.ptt.cc/bbs/Gossiping/M.1694829290.A.9F1.html'}}) "
                 f"MATCH (commenter)-[:RESPONDS]->(a5) "
                 f"MATCH (commenter)-[:USES]->(ip:Commenter_ip) "
                 f"RETURN *")
        results = graph.run(query).data()

        G = nx.Graph()
        for record in results:
            a1 = record['a1']['article']
            a2 = record['a2']['article']
            a3 = record['a3']['article']
            a4 = record['a4']['article']
            a5 = record['a5']['article']
            commenter = record['commenter']['id']
            ip = record['ip']['ip']

            G.add_node(a1, type='Article')
            G.add_node(a2, type='Article')
            G.add_node(a3, type='Article')
            G.add_node(a4, type='Article')
            G.add_node(a5, type='Article')
            G.add_node(commenter, type='Commenter')
            G.add_node(ip, type='IP')
            G.add_edge(a1, commenter, type='RESPONDS')
            G.add_edge(a2, commenter, type='RESPONDS')
            G.add_edge(a3, commenter, type='RESPONDS')
            G.add_edge(a4, commenter, type='RESPONDS')
            G.add_edge(a5, commenter, type='RESPONDS')
            G.add_edge(commenter, ip, type='USES')

        pos = nx.spring_layout(G)

        colors = [
            '#1f78b4' if G.nodes[node]['type'] == 'Article' else '#33a02c' if G.nodes[node]['type'] == 'IP' else '#fb9a99'
            for node in G.nodes]

        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(width=0.5, color='#888'),
        )

        node_x = [pos[k][0] for k in pos]
        node_y = [pos[k][1] for k in pos]

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            marker=dict(
                showscale=False,
                size=10,
                color=colors,  # Node color changes based on the type
                opacity=0.8
            )
        )

        figure = go.Figure(data=[edge_trace, node_trace],
                           layout=go.Layout(
                               showlegend=False,
                               hovermode='closest',
                               margin=dict(b=0, l=0, r=0, t=0),
                               xaxis=dict(showgrid=False, zeroline=False),
                               yaxis=dict(showgrid=False, zeroline=False))
                           )

        annotations = []
        for node, (x, y) in pos.items():
            node_type = G.nodes[node]['type']
            if node_type == 'Article':
                display_text = node
            elif node_type == 'IP':
                display_text = node
            elif node_type == 'Commenter':
                display_text = node
            else:
                display_text = node_type
            annotations.append(
                go.layout.Annotation(
                    x=x,
                    y=y,
                    xref="x",
                    yref="y",
                    text=display_text,
                    showarrow=False,
                    font=dict(size=10)
                )
            )
        figure.update_layout(annotations=annotations)
        return figure, {'display': 'block'}


    @app.callback(
        [Output('wordcloud-graph', 'src'),
         Output('wordcloud-graph', 'style')],
        [Input('submit-button', 'n_clicks')],
        [dash.dependencies.State('account-id', 'value')]
    )
    def wordcloud_graph(n_clicks, account_id):
        if n_clicks is None or not account_id:
            return dash.no_update, {'display': 'none'}

        gossip_collection, politics_collection, all_comments = db["gossip"], db["politics"], []

        gossip_cursor = gossip_collection.find({"article_data.comments.commenter_id": account_id},
                                               {'article_data.comments': 1, "article_url": 1, "_id": 0})
        politic_cursor = politics_collection.find({"article_data.comments.commenter_id": account_id},
                                                  {'article_data.comments': 1, "article_url": 1, "_id": 0})

        for article in gossip_cursor:
            for comment in article["article_data"]["comments"]:
                if comment["commenter_id"] == account_id:
                    all_comments.append(comment["comment_content"])

        for article in politic_cursor:
            for comment in article["article_data"]["comments"]:
                if comment["commenter_id"] == account_id:
                    all_comments.append(comment["comment_content"])

        wc = WordCloud(font_path=TC_FONT_PATH, margin=2, background_color="white", max_font_size=150,
                       width=980, height=600).generate(" ".join(all_comments))

        return wc.to_image(), {'display': 'block'}

    return app

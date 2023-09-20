import os
import dash
import networkx as nx
from py2neo import Graph
from dotenv import load_dotenv
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
from plotly.graph_objs import Scatter3d, Line
from data_processing.aggregate_mongo import count_articles, count_comments, count_accounts

load_dotenv(verbose=True)

graph = Graph(uri=f"{os.getenv('NEO4J_URL')}:7687",
              auth=(os.getenv("NEO4J_USERNAME", "YourAccount"), os.getenv("NEO4J_PASSWORD", "YourPassword")))

app = dash.Dash(__name__)

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
    html.Script("""
            setTimeout(function() {
                var canvas = document.querySelector("canvas");
                if (canvas) {
                    canvas.setAttribute("willReadFrequently", "true");
                }
            }, 5000);
        """)
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
            html.H6('Crawled Article Count', style={'textAlign': 'center'}),
            html.H1(f'{total_articles}', style={'textAlign': 'center'}),
            html.H6('Articles', style={'textAlign': 'center'})
        ], style={'width': '33%', 'display': 'inline-block'}),

        html.Div([
            html.H6('Crawled Comment Count', style={'textAlign': 'center'}),
            html.H1(f'{total_comments}', style={'textAlign': 'center'}),
            html.H6('Comments', style={'textAlign': 'center'})
        ], style={'width': '33%', 'display': 'inline-block'}),

        html.Div([
            html.H6('Crawled Account Count', style={'textAlign': 'center'}),
            html.H1(f'{total_accounts}', style={'textAlign': 'center'}),
            html.H6('Accounts', style={'textAlign': 'center'})
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
             f"MATCH (commenter)-[:USES]->(ip:Commenter_ip) "
             f"RETURN *")
    results = graph.run(query).data()

    print(f"results: {results}")

    G = nx.Graph()
    pos = nx.spring_layout(G, dim=3)  # Set dim=3 for 3D layout

    for record in results:
        a1 = record['a1']['article']
        a2 = record['a2']['article']
        commenter = record['commenter']['id']
        ip = record['ip']['ip']

        G.add_node(a1, type='Article')
        G.add_node(a2, type='Article')
        G.add_node(commenter, type='Commenter')
        G.add_node(ip, type='IP')
        G.add_edge(a1, commenter, type='RESPONDS')
        G.add_edge(a2, commenter, type='RESPONDS')
        G.add_edge(commenter, ip, type='USES')

    print("Nodes in the graph:", G.nodes())  # Debug point 3

    # pos = nx.spring_layout(G)


    # Different colors for different node types
    colors = [
        '#1f78b4' if G.nodes[node]['type'] == 'Article' else '#33a02c' if G.nodes[node]['type'] == 'IP' else '#fb9a99'
        for node in G.nodes]

    # edge_x = []
    # edge_y = []
    # for edge in G.edges():
    #     x0, y0 = pos[edge[0]]
    #     x1, y1 = pos[edge[1]]
    #     edge_x.extend([x0, x1, None])
    #     edge_y.extend([y0, y1, None])
    #
    # edge_trace = go.Scatter(
    #     x=edge_x, y=edge_y,
    #     mode='lines',
    #     line=dict(width=0.5, color='#888'),
    # )
    #
    # node_x = [pos[k][0] for k in pos]
    # node_y = [pos[k][1] for k in pos]
    #
    # node_trace = go.Scatter(
    #     x=node_x, y=node_y,
    #     mode='markers',
    #     marker=dict(
    #         showscale=False,
    #         size=10,
    #         color=colors,  # Node color changes based on the type
    #         opacity=0.8
    #     )
    # )
    #
    # figure = go.Figure(data=[edge_trace, node_trace],
    #                    layout=go.Layout(
    #                        showlegend=False,
    #                        hovermode='closest',
    #                        margin=dict(b=0, l=0, r=0, t=0),
    #                        xaxis=dict(showgrid=False, zeroline=False),
    #                        yaxis=dict(showgrid=False, zeroline=False))
    #                    )
    #
    # annotations = []
    # for node, (x, y) in pos.items():
    #     node_type = G.nodes[node]['type']
    #     if node_type == 'Article':
    #         display_text = node
    #     elif node_type == 'IP':
    #         display_text = node
    #     elif node_type == 'Commenter':
    #         display_text = node
    #     else:
    #         display_text = node_type
    #     annotations.append(
    #         go.layout.Annotation(
    #             x=x,
    #             y=y,
    #             xref="x",
    #             yref="y",
    #             text=display_text,
    #             showarrow=False,
    #             font=dict(size=10)
    #         )
    #     )
    # figure.update_layout(annotations=annotations)
    # return figure, {'display': 'block'}

    edge_x = []
    edge_y = []
    edge_z = []
    for edge in G.edges():
        # Debug point 2
        if edge[0] not in pos or edge[1] not in pos:
            print(f"Skipping edge from {edge[0]} to {edge[1]}")
            continue

        # Debug point 3
        if len(pos[edge[0]]) != 3 or len(pos[edge[1]]) != 3:
            print(f"Unexpected position format for {edge[0]} or {edge[1]}")
            continue
        try:
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
        except ValueError as e:
            print(f"ValueError occurred: {e}")
            print("Position for edge[0]:", pos.get(edge[0], "Not found"))
            print("Position for edge[1]:", pos.get(edge[1], "Not found"))
            continue
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    edge_trace = Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode='lines',
        line=Line(width=0.5, color='#888'),
        hoverinfo='none'
    )

    node_x = [pos[k][0] for k in pos]
    node_y = [pos[k][1] for k in pos]
    node_z = [pos[k][2] for k in pos]

    node_trace = Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers',
        marker=dict(
            showscale=False,
            size=6,
            color=colors,  # Node color changes based on the type
            opacity=0.8
        )
    )

    figure = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           scene=dict(
                               xaxis=dict(nticks=4, range=[-1, 1]),
                               yaxis=dict(nticks=4, range=[-1, 1]),
                               zaxis=dict(nticks=4, range=[-1, 1])
                           ),
                           margin=dict(
                               l=0,
                               r=0,
                               b=0,
                               t=0
                           ),
                           showlegend=False,
                           hovermode='closest'
                       )
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


if __name__ == '__main__':
    app.run_server(debug=True)

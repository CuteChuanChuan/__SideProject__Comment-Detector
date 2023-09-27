from dash import html
from .utils_mongodb import count_articles, count_comments, count_accounts


def update_layout():
    total_articles = count_articles("gossip") + count_articles("politics")
    total_comments = count_comments("gossip") + count_comments("politics")
    total_accounts = count_accounts("gossip") + count_accounts("politics")

    return [
        html.Div(
            [
                html.H4("Crawled Article Count", style={"textAlign": "center"}),
                html.H1(f"{total_articles:,}", style={"textAlign": "center"}),
                html.H5("Articles", style={"textAlign": "center"}),
            ],
            style={"width": "33%", "display": "inline-block"},
        ),
        html.Div(
            [
                html.H4("Crawled Comment Count", style={"textAlign": "center"}),
                html.H1(f"{total_comments:,}", style={"textAlign": "center"}),
                html.H5("Comments", style={"textAlign": "center"}),
            ],
            style={"width": "33%", "display": "inline-block"},
        ),
        html.Div(
            [
                html.H4("Crawled Account Count", style={"textAlign": "center"}),
                html.H1(f"{total_accounts:,}", style={"textAlign": "center"}),
                html.H5("Accounts", style={"textAlign": "center"}),
            ],
            style={"width": "33%", "display": "inline-block"},
        ),
    ]

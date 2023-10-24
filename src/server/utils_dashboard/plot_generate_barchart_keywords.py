import plotly.graph_objects as go
from utils_dashboard.func_get_keyword_from_text import (
    extract_top_n_keywords,
    retrieve_top_n_keywords,
    NUM_KEYWORDS,
)


def generate_barchart_keywords(
    target_collection: str, n_days: int, source: str
) -> go.Figure:
    keyword_data = retrieve_top_n_keywords(
        target_collection=target_collection, n_days=n_days, source=source
    )
    labels, values = zip(*keyword_data)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=values, marker=dict(color="rgb(55, 83, 109)")))
    board_info_zh = "八卦" if target_collection == "gossip" else "政黑"
    fig.update_layout(
        title=f"{board_info_zh}版 | 過去{n_days}天 | {source}的{NUM_KEYWORDS}個關鍵字",
        yaxis_title="權重",
    )
    return fig

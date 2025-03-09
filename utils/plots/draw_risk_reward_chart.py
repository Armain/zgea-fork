import plotly.graph_objects as go
import pandas as pd
from typeguard import typechecked


@typechecked()
def draw_risk_reward_chart(
        data: pd.DataFrame,
        title: str,
        x_title: str = "Risk",
        y_title: str = "Reward",
):
    layout = go.Layout(
        title=title,
        xaxis=dict(
            title=x_title,
        ),
        yaxis=dict(
            title=y_title,
        ),
    )
    fig = go.Figure(layout=layout)
    for n, d in data.iterrows():
        fig.add_trace(go.Scatter(
            x = [d.risk],
            y = [d.reward],
            name = n,
            marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')),
            mode='markers+text',
            textposition="top center",
            text = n,
        ))
    fig.show()

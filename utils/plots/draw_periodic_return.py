import pandas as pd
import plotly.graph_objects as go
from typeguard import typechecked
from typing import Dict
from plotly.subplots import make_subplots


@typechecked()
def draw_periodic_return(
        data: Dict[str, pd.Series],
        title: str,
        x_title: str = "time",
        y_title: str = "return in %",
        show: bool = True
):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for n, d in data.items():
        fig.add_trace(go.Bar(
            x = d.index,
            y = d * 100,
            name = n
        ))

    fig.update_xaxes(title_text=x_title)
    fig.update_yaxes(title_text=y_title)
    fig.update_layout(
        title = title,
    )
    if show:
        fig.show()
    else:
        return fig

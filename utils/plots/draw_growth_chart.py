from typing import Dict, Optional, List
import plotly.graph_objects as go
import pandas as pd
from typeguard import typechecked
from plotly.subplots import make_subplots


@typechecked()
def draw_growth_chart(
        data: Dict[str, pd.Series],
        name: str = "Growth Chart",
        y_title: str = "growth",
        x_title: str = "years",
        y_log: bool = True,
        y_range: Optional[List[float]] = None,
        overlapping_only: bool = False,
        show = True,
):
    if overlapping_only:
        first_common_date = max([min(d.index) for d in data.values()])
        last_common_date = min([max(d.index) for d in data.values()])

        new_data = {}
        for n, d in data.items():
            new_data[n] = d.loc[first_common_date:last_common_date]

        data = new_data


    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for n, d in data.items():
        fig.add_trace(go.Scatter(
            x=d.index,
            y=d,
            mode='lines',
            name=n,
        ))

    if y_range is not None:
        fig.update_yaxes(range=y_range)

    fig.update_xaxes(title_text=x_title)
    fig.update_yaxes(title_text=y_title, type="log" if y_log == True else "linear")
    fig.update_layout(
        title = name,
    )
    if show:
        fig.show()
    else:
        return fig

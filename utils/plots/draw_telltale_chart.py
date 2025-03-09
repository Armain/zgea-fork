import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Optional, List
from typeguard import typechecked


@typechecked()
def draw_telltale_chart(
        reference: pd.Series,
        data: Dict[str, pd.Series],
        name: str = "Growth Chart",
        y_title: str = "relative performance in %",
        y_log: bool = False,
        y_range: Optional[List[float]] = None,
        overlapping_only: bool = False,
):
    if overlapping_only:
        all_data = list(data.values()) + [reference]
        first_common_date = max([min(d.index) for d in all_data])
        last_common_date = min([max(d.index) for d in all_data])

        new_data = {}
        for n, d in data.items():
            new_data[n] = d.loc[first_common_date:last_common_date]

        data = new_data
        reference = reference.loc[first_common_date:last_common_date]

    layout = go.Layout(
        title=name,
        xaxis=dict(
            title='years',
        ),
        yaxis=dict(
            title=y_title,
            type="log" if y_log else "linear",
        ),
    )
    fig = go.Figure(layout=layout)
    fig.add_trace(go.Scatter(
        x=reference.index,
        y=(reference / reference - 1),
        mode='lines',
        name="reference",
    ))
    for n, d in data.items():
        fig.add_trace(go.Scatter(
            x=d.index,
            y=(d / reference - 1)*100,
            mode='lines',
            name=n,
        ))

    if y_range is not None:
        fig.update_yaxes(range=y_range)

    fig.show()

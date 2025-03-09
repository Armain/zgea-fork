import pandas as pd
import plotly.graph_objs as go
from typing import Optional
from typeguard import typechecked


@typechecked
def draw_monte_carlo_simulation(
        simulation: pd.DataFrame,
        simulation_name: str,
        reference: Optional[pd.Series] = None,
        reference_name: Optional[str] = None,
        name: Optional[str] = None,
        x_title: str = "days",
        y_title: str = "value in $",
        y_log = True,
        draw_stddev = False,
        draw_minmax = False,
):
    years = int(len(simulation.index)/365)
    sim_string = f"[{simulation_name}] ({years} years)"
    if name is None:
        name = f"Growth in {years} years"

    colour = 'rgba(0,0,100,{a})'
    reference_colour = 'rgba(100,0, 0,{a})'

    plot_list = []
    plot_list.append(
        go.Scatter(
            x=simulation.index,
            y=simulation['mean'],
            line=dict(color=colour.format(a=1)),
            mode='lines',
            name=simulation_name,
        )
    )
    sim_string += f"\n * average: ${simulation.iloc[-1]['mean']:.2f}"

    if draw_stddev:
        plot_list.append(
            go.Scatter(
                x=simulation.index,
                y=simulation['stddev_low'],
                line=dict(color=colour.format(a=0.2)),
                mode='lines',
                showlegend=False
            )
        )
        plot_list.append(
            go.Scatter(
                x=simulation.index,
                y=simulation['stddev_up'],
                line=dict(color=colour.format(a=0.2)),
                mode='lines',
                showlegend=False
            )
        )
        plot_list.append(
            go.Scatter(
                x=list(simulation.index)+list(simulation.index)[::-1],
                y=list(simulation['stddev_up'])+list(simulation['stddev_low'])[::-1],
                fill='toself',
                fillcolor=colour.format(a=0.2),
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=False
            )
        )
        sim_string += f"\n * 95% confidence interval: ${simulation.iloc[-1]['stddev_low']:.2f} to ${simulation.iloc[-1]['stddev_up']:.2f}"

    if draw_minmax:
        plot_list.append(
            go.Scatter(
                x=simulation.index,
                y=simulation['min'],
                line=dict(color=colour.format(a=0.2)),
                mode='lines',
                showlegend=False
            )
        )
        plot_list.append(
            go.Scatter(
                x=simulation.index,
                y=simulation['max'],
                line=dict(color=colour.format(a=0.2)),
                mode='lines',
                showlegend=False
            )
        )
        plot_list.append(
            go.Scatter(
                x=list(simulation.index)+list(simulation.index)[::-1],
                y=list(simulation['max'])+list(simulation['min'])[::-1],
                fill='toself',
                fillcolor=colour.format(a=0.2),
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=False
            )
        )
        sim_string += f"\n * 100% interval: ${simulation.iloc[-1]['min']:.2f} to ${simulation.iloc[-1]['max']:.2f}"

    if reference is not None:
        plot_list.append(
            go.Scatter(
                x=reference.index,
                y=reference,
                line=dict(color=reference_colour.format(a=1)),
                mode='lines',
                name=reference_name,
            )
        )

    fig = go.Figure(plot_list)

    fig.update_xaxes(title_text=x_title)
    fig.update_yaxes(title_text=y_title, type="log" if y_log == True else "linear")
    fig.update_layout(title = name)

    fig.show()

    print(sim_string)
    if reference is not None:
        print(f"[{reference_name}] ({years} years) ${reference.iloc[-1]:.2f}")

from dash import Dash, html
from pathlib import Path
from .components import (
    pie_expt_types,
    scale_switcher_button,
    coverage_by_expt,
    selectable_scatter,
    selectables_dropdowns,
)

LOGO_PATH = "assets/warehouse_logo.png"


def create_layout(
    app: Dash, sample_data, experiment_data, sequence_data, combined_data
) -> html.Div:
    return html.Div(
        # className="app-div",
        children=[
            html.Img(src=LOGO_PATH),
            html.Hr(),
            html.H2("Throughput:"),
            pie_expt_types.render(app, sample_data, experiment_data),
            html.Hr(),
            coverage_by_expt.render(app, sequence_data),
            scale_switcher_button.render(app),
            html.Hr(),
            selectables_dropdowns.render(app, combined_data),
            selectable_scatter.render(app, combined_data),
        ]
    )

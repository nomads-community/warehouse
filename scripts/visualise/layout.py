from dash import Dash, html, dcc
from pathlib import Path
from .components import (
    pie_expt_types,
    scale_switcher_button,
    coverage_by_expt,
    selectable_scatter,
    selectables_dropdowns
)
from lib.dataschemas import DataSources

LOGO_PATH = "assets/warehouse_logo.png"

def create_layout(app: Dash, sample_class, experiment_class, sequence_class, alldata_df) -> html.Div:
    
    return html.Div(
        # className="app-div",
        children=[
            html.Img(src=LOGO_PATH),
            html.Hr(),
            html.H2("Throughput:"),
            pie_expt_types.render(app, sample_class, experiment_class),
            html.Hr(),
            coverage_by_expt.render(app, sequence_class.summary_bam),
            scale_switcher_button.render(app),
            html.Hr(),
            selectables_dropdowns.render(app),
            selectable_scatter.render(app, alldata_df),
        ]
    )
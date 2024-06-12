from dash import Dash, html, dcc
import pandas as pd
from .components import (
    pie_expt_types,
    scale_switcher_button,
    coverage_by_expt
)


CSS_STYLE = ["assets/calling-style.css"]
LOGO_PATH = '"/assets/warehouse_logo.png"'

def create_layout(app: Dash, sample_class, experiment_class, sequence_class) -> html.Div:
    
    return html.Div(
        className="app-div",
        children=[
            html.H1(app.title),
            html.Img(src=LOGO_PATH),
            html.Hr(),
            html.H2("Throughput:"),
            pie_expt_types.render(app, sample_class, experiment_class),
            html.Hr(),
            coverage_by_expt.render(app, sequence_class.summary_bam),
            scale_switcher_button.render(app)
        ]
    )

# TO DO
# Add classnames to the items to apply css modifications
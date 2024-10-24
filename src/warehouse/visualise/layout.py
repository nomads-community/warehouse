from dash import Dash, html
from .components import (
    banner,
    pie_expt_types,
    seq_qc_by_expt,
    selectable_scatter,
    )
   
def create_layout(app: Dash, 
                  sample_data, 
                  experiment_data, 
                  sequence_data, 
                  combined_data) -> html.Div:
    """
    Return the webpage
    """
    
    return html.Div(
        className="entire",
        children=[
            banner.render(app),
            pie_expt_types.render(app, sample_data, experiment_data),
            seq_qc_by_expt.render_qc_panel(app, sequence_data),
            selectable_scatter.render(app, combined_data),
        ]
    )
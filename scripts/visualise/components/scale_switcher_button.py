from dash import Dash, html, dcc
from dash.dependencies import Input, Output
from . import ids

def render(app: Dash) -> html.Div:
    @app.callback(
        Output(ids.SEQ_OUTPUT_SCALE_BUTTON, 'children'),
        Input(ids.SEQ_OUTPUT_SCALE_BUTTON, 'n_clicks')
    )
    def update_scale_and_text(n_clicks: int) -> str:    
        if n_clicks % 2 == 0:
            return "Linear"
        return "Log"
    
    return html.Div(
        children=[
            html.Button(
                id=ids.SEQ_OUTPUT_SCALE_BUTTON,
                n_clicks=0,
            )
        ]
    )
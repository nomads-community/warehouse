from dash import Dash, html

def render(app: Dash):
    LOGO_PATH = "../assets/warehouse_logo.png"
    return html.Div(
        className="banner",
        children=[html.Img(src=LOGO_PATH)]
    )
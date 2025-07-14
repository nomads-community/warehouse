from dash import Dash, html

from warehouse.configure.configure import get_configuration_value


def render(app: Dash) -> html.Div:
    LOGO_PATH = "../assets/warehouse_logo.png"

    sample_set = get_configuration_value("shared_sample_file").stem
    group_name = get_configuration_value("group_name")
    return html.Div(
        className="banner",
        children=[
            html.Img(src=LOGO_PATH, height=80),
            html.H1(f"{group_name} sequence data from the {sample_set} samples"),
        ],
    )

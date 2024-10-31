from dash import Dash, html

def render(app: Dash, cli_flags: list[str]) -> html.Div:
    
    LOGO_PATH = "../assets/warehouse_logo.png"
    exp_folder = cli_flags[0]
    seq_folder = cli_flags[1]
    metadata_file = cli_flags[2]

    return html.Div(
        className="banner",
        children=[html.Img(src=LOGO_PATH, height=80),
                  html.P(
                         [
                             f"Experiment folder: {exp_folder}",
                             html.Br(),
                             f"Sequence folder: {seq_folder}",
                             html.Br(),
                             f"Metadata file:   {metadata_file}",
                         ])]
    )

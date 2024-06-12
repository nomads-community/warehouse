from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from . import ids


def datasource(app: Dash, component_number : int) -> html.Div:
    #List of data sources
    #TO ADD: This should be dynamic based on what the user passes to the system
    datasources = ["Sample", "Experiment", "Sequence"]

    return html.Div(
        children=[
            html.H6("Select DataSource"),
            dcc.Dropdown(
                id=f"{ids.DATASOURCE_DROPDOWN}_{component_number}",
                options=[{"label": datasource, "value": datasource } for datasource in datasources],
                value=datasources,
                multi=False,
            ),
           
        ]
    )

def target(app: Dash, component_number : int) -> html.Div:
    #List of columns
    columns = ["Parasitaemia", "Location", "Other"]

    # @app.callback(
    #     Output(f"{ids.COLUMN_DROPDOWN}_{component_number}", "value"),
    #     Input(f"{ids.DATASOURCE_DROPDOWN}_{component_number}", "value")
    #     )
    
    return html.Div(
        children=[
            html.H6("Select Column"),
            dcc.Dropdown(
                id=f"{ids.COLUMN_DROPDOWN}_{component_number}",
                options=[{"label": col, "value": col } for col in columns],
                value=columns,
                multi=False,
            ),
           
        ]
    )
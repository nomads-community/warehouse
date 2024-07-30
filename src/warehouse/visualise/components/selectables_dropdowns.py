from dash import Dash, html, dcc, Input, Output
from . import ids


def create_dropdown(
    app: Dash, dropdown_id_prefix: str, dropdown_number: int, options: dict
) -> dcc.Dropdown:
    """
    Creates a dropdown with options that can be dynamically updated.

    Args:
        app (Dash): The Dash app instance.
        dropdown_id_prefix (str): The prefix for the dropdown ID (e.g., "list_dropdown").
        dropdown_number (int): The sequential number for the dropdown (starting from 1).
        options (dict): Dictionary containing the key value pairs to show user and value for each selection

    Returns:
        dcc.Dropdown: The created dropdown component.
    """

    dropdown_id = f"{dropdown_id_prefix}_{dropdown_number}"
    return dcc.Dropdown(id=dropdown_id, options=options, className="wide_dropdown")


# def get_list_from_dict ():


def render(app: Dash, combined_data: object):
    """
    Renders identical dropdowns with sequential numbering.

    Args:
        app (Dash): The Dash app instance.
    """

    @app.callback(
        [
            Output(
                component_id=ids.COLUMN_DROPDOWN + "_1", component_property="options"
            ),
            Output(
                component_id=ids.COLUMN_DROPDOWN + "_2", component_property="options"
            ),
            Output(
                component_id=ids.COLUMN_DROPDOWN + "_3", component_property="options"
            ),
        ],
        [
            Input(
                component_id=ids.DATASOURCE_DROPDOWN + "_1", component_property="value"
            ),
            Input(
                component_id=ids.DATASOURCE_DROPDOWN + "_2", component_property="value"
            ),
            Input(
                component_id=ids.DATASOURCE_DROPDOWN + "_3", component_property="value"
            ),
        ],
    )
    def update_dropdowns(select1, select2, select3):
        # Return the selection made to populate the dropdown with appropriate dict
        return [
            combined_data.datasource_fields.get(select1, ["Select datasource first"]),
            combined_data.datasource_fields.get(select2, ["Select datasource first"]),
            combined_data.datasource_fields.get(select3, ["Select datasource first"]),
        ]

    combined_data
    dropdown1 = create_dropdown(
        app, ids.DATASOURCE_DROPDOWN, 1, combined_data.datasources_dict
    )
    dropdown2 = create_dropdown(
        app, ids.DATASOURCE_DROPDOWN, 2, combined_data.datasources_dict
    )
    dropdown3 = create_dropdown(
        app, ids.DATASOURCE_DROPDOWN, 3, combined_data.datasources_dict
    )

    dynamic1 = create_dropdown(app, ids.COLUMN_DROPDOWN, 1, ["Select datasource first"])
    dynamic2 = create_dropdown(app, ids.COLUMN_DROPDOWN, 2, ["Select datasource first"])
    dynamic3 = create_dropdown(app, ids.COLUMN_DROPDOWN, 3, ["Select datasource first"])

    return html.Div(
        children=[
            html.Div(  # Outer container
                style={
                    "display": "flex",
                    "flex-wrap": "wrap",
                    "align-items": "center",
                    "justify-content": "space-around",
                },
                children=[
                    html.Div(  # group 1
                        style={
                            "display": "flex",
                            "flex-direction": "column",
                            "align-items": "center",
                        },
                        children=[
                            html.Div(children=["Select x axis"]),
                            dropdown1,
                            dynamic1,
                        ],
                    ),
                    html.Div(  # group 2
                        style={
                            "display": "flex",
                            "flex-direction": "column",
                            "align-items": "center",
                        },
                        children=[
                            html.Div(children=["Select y axis"]),
                            dropdown2,
                            dynamic2,
                        ],
                    ),
                    html.Div(  # group 3
                        style={
                            "display": "flex",
                            "flex-direction": "column",
                            "align-items": "center",
                        },
                        children=[
                            html.Div(children=["Select colour variable"]),
                            dropdown3,
                            dynamic3,
                        ],
                    ),
                ],
            ),
        ]
    )

from dash import Dash, html, dcc, Input, Output
import plotly.express as px
from . import ids
import logging

#Define logging process
log = logging.getLogger("selectable_scatter")


def create_scatter(all_data: object,
                   x_series=None, 
                   y_series=None, 
                   colour_series=None) -> px.scatter:
    
    # Define the dataschemadict and the field-label dict
    DataSchema = all_data.dataschema_dict
    FieldLabels = all_data.all_field_labels

    # Define a default set of values in case none are passed
    if x_series is None:
        x_series = DataSchema["PCR_PRODUCT"]["field"]
    if y_series is None:
        y_series = DataSchema["N_PRIMARY"]["field"]
    if colour_series is None:
        colour_series = DataSchema["EXP_ID"]["field"] + "_seqlib"

    # Filter the data so that there are no empty values
    df = all_data.df
    # Slice the data to the three key columns
    dff = df[[x_series, y_series, colour_series]].copy(deep=True)
    # Drop in place
    dff.dropna(axis=0, how="any", inplace=True)
    dff.mask(dff.eq("None")).dropna(axis=0, how="any", inplace=True)

    log.info(
        f"Plotting x: {x_series}, y: {y_series}, colour: {colour_series}, df shape ={dff.shape}"
    )

    # Plot the values
    fig = px.scatter(dff, x=x_series, y=y_series, color=colour_series)

    fig.update_yaxes(title=FieldLabels.get(y_series))
    fig.update_xaxes(title=FieldLabels.get(x_series))
    fig.update_layout(legend_title_text=FieldLabels.get(colour_series))

    return fig


def render(app: Dash, combined_data):
    @app.callback(
        Output(ids.SELECTABLE_SCATTER, "figure"),
        [
            Input(ids.DYNAMIC_OPTIONS + "_1", "value"),
            Input(ids.DYNAMIC_OPTIONS + "_2", "value"),
            Input(ids.DYNAMIC_OPTIONS + "_3", "value"),
        ],
    )
    def update_scatter(dd1, dd2, dd3) -> px.scatter:
        fig = create_scatter(
            combined_data, x_series=dd1, y_series=dd2, colour_series=dd3
        )
        return fig

    # Build initial graph
    dropdowns=dropdowns_panel(app, combined_data)
    fig = create_scatter(combined_data)

    return html.Div(
        className="panel",
        children=[
            html.H2("Selectable data:"),
            dropdowns,
            dcc.Graph(figure=fig, id=ids.SELECTABLE_SCATTER)
        ]
        )

def create_dropdown_set(number: int, options: dict) -> html.Div:
    """
    Creates a double dropdown with options that can be dynamically updated.

    Args:
        dropdown_number (int): The sequential number for the dropdown (starting from 1).
        options (dict): Dictionary containing the key value pairs to show user and value for each selection

    Returns:
        dcc.Dropdown: The created dropdown component.
    """
    static = dcc.Dropdown(id=f"{ids.DATASOURCES}_{number}",
                          options=options,
                          className="wide_dropdown")
    dynamic = dcc.Dropdown(id=f"{ids.DYNAMIC_OPTIONS}_{number}",
                          options=options,
                          className="wide_dropdown")
    axes = [ "Select x axis", "Select y axis", "Select colour"]
    return html.Div(
        className="dropdown-fill",
        children=[
            axes[number-1],
            static,
            dynamic
            ]
            )


def dropdowns_panel(app: Dash, all_data: object) -> html.Div:
    """
    Renders dropdowns for x, y and colour axes

    Args:
        app (Dash): The Dash app instance.
    """

    @app.callback(
        [
            Output(ids.DYNAMIC_OPTIONS + "_1", "options"),
            Output(ids.DYNAMIC_OPTIONS + "_2", "options"),
            Output(ids.DYNAMIC_OPTIONS + "_3", "options"),
        ],
        [
            Input(ids.DATASOURCES + "_1", "value"),
            Input(ids.DATASOURCES + "_2", "value"),
            Input(ids.DATASOURCES + "_3", "value"),
        ],
    )
    def update_dropdowns(select1, select2, select3):
        # Return the selection made to populate the dropdown with appropriate dict
        return [
            all_data.datasource_fields.get(select1, ["Select datasource first"]),
            all_data.datasource_fields.get(select2, ["Select datasource first"]),
            all_data.datasource_fields.get(select3, ["Select datasource first"]),
        ]
    
    dropdown1 = create_dropdown_set(1, all_data.datasources_dict)
    dropdown2 = create_dropdown_set(2, all_data.datasources_dict)
    dropdown3 = create_dropdown_set(3, all_data.datasources_dict)

    return html.Div(
        className="row-flex",
        children=[dropdown1,
                  dropdown2,
                  dropdown3
                  ]
    )
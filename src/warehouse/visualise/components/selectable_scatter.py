import logging
from pathlib import Path

import plotly.express as px
from dash import Dash, Input, Output, dcc, html

from warehouse.lib.dictionaries import reformat_nested_dict

from . import ids

# Define logging process
log = logging.getLogger(Path(__file__).stem)


def create_scatter(
    all_data: object, x_series=None, y_series=None, colour_series=None
) -> px.scatter:
    # Define the dataschemadict and the field-label dict
    DataSchema = all_data.dataschema
    FieldLabels = reformat_nested_dict(all_data.dataschema, "field", "label")

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

    log.debug(
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
        Output(ids.SCATPLOT, "figure"),
        [
            Input(ids.SCATPLOT_FIELD + "_1", "value"),
            Input(ids.SCATPLOT_FIELD + "_2", "value"),
            Input(ids.SCATPLOT_FIELD + "_3", "value"),
        ],
    )
    def update_scatter(field_x, field_y, field_col) -> px.scatter:
        fig = create_scatter(
            combined_data, x_series=field_x, y_series=field_y, colour_series=field_col
        )
        return fig

    # Build initial graph
    dropdowns = dropdowns_panel(app, combined_data)
    fig = create_scatter(combined_data)

    return html.Div(
        className="panel",
        children=[
            html.H2("Selectable data:"),
            dropdowns,
            dcc.Graph(figure=fig, id=ids.SCATPLOT),
        ],
    )


def create_dropdown_set(
    number: int, category_opts: dict, source_opts: dict, field_opts: dict
) -> html.Div:
    """
    Creates a col of dropdowns with options that can be dynamically updated.

    Args:
        number (int): The sequential number for the dropdown (starting from 1).
        source_options (dict): Dictionary containing the key value pairs to show user and value for source
        field_options (dict): Dictionary containing the key value pairs to show user and value for field

    Returns:
        dcc.Dropdown: The created dropdown component.
    """
    category = dcc.Dropdown(
        id=f"{ids.SCATPLOT_CATEGORY}_{number}",
        options=category_opts,
        className="wide_dropdown",
        placeholder="Select a data category",
    )
    source = dcc.Dropdown(
        id=f"{ids.SCATPLOT_SOURCE}_{number}",
        options=source_opts,
        className="wide_dropdown",
        placeholder="Select a data source",
    )
    field = dcc.Dropdown(
        id=f"{ids.SCATPLOT_FIELD}_{number}",
        options=field_opts,
        className="wide_dropdown",
        placeholder="Select a data field",
    )
    col_headers = ["x axis selection", "y axis selection", "colour selection"]

    # Build the dropdown col
    dropdown_col = []
    dropdown_col.append(
        html.Label(
            col_headers[number - 1],
            style={"fontWeight": "bold", "textAlign": "center", "display": "block"},
        )
    )
    dropdown_col.append(category)
    dropdown_col.append(source)
    dropdown_col.append(field)
    return html.Div(className="dropdown-fill", children=dropdown_col)


def dropdowns_panel(app: Dash, all_data: object) -> html.Div:
    """
    Renders dropdowns for x, y and colour axes

    Args:
        app (Dash): The Dash app instance.
    """

    @app.callback(
        [
            Output(ids.SCATPLOT_SOURCE + "_1", "options"),
            Output(ids.SCATPLOT_SOURCE + "_2", "options"),
            Output(ids.SCATPLOT_SOURCE + "_3", "options"),
            Output(ids.SCATPLOT_FIELD + "_1", "options"),
            Output(ids.SCATPLOT_FIELD + "_2", "options"),
            Output(ids.SCATPLOT_FIELD + "_3", "options"),
        ],
        [
            Input(ids.SCATPLOT_CATEGORY + "_1", "value"),
            Input(ids.SCATPLOT_CATEGORY + "_2", "value"),
            Input(ids.SCATPLOT_CATEGORY + "_3", "value"),
            Input(ids.SCATPLOT_SOURCE + "_1", "value"),
            Input(ids.SCATPLOT_SOURCE + "_2", "value"),
            Input(ids.SCATPLOT_SOURCE + "_3", "value"),
        ],
    )
    def update_dropdowns(cat1, cat2, cat3, source1, source2, source3):
        # Return the selection made to populate the dropdown with appropriate dict
        sources = all_data.sources
        fields = all_data.fields
        log.debug(f"source1: {source1}, return: {fields.get(source1)}")
        log.debug(f"source2: {source2}, return: {fields.get(source2)}")
        log.debug(f"source3: {source3}, return: {fields.get(source3)}")
        return [
            sources.get(cat1, source_list),
            sources.get(cat2, source_list),
            sources.get(cat3, source_list),
            fields.get(source1, field_list),
            fields.get(source2, field_list),
            fields.get(source3, field_list),
        ]

    # Define default entries for the dropdowns

    cat_list = all_data.categories
    source_list = ["Select category first (above)"]
    field_list = ["Select source first (above)"]

    col1 = create_dropdown_set(1, cat_list, source_list, field_list)
    col2 = create_dropdown_set(2, cat_list, source_list, field_list)
    col3 = create_dropdown_set(3, cat_list, source_list, field_list)

    return html.Div(className="row-flex", children=[col1, col2, col3])

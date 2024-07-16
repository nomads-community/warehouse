from dash import Dash, html, dcc, Input, Output
import plotly.express as px
from . import ids
import numpy as np
import pandas as pd

def create_scatter(combined_data : object, x_series = None, y_series = None, colour_series = None):
    
    #Define the dataschemadict and the field-label dict
    DataSchema = combined_data.dataschema_dict
    FieldLabels = combined_data.all_field_labels

    #Define a default set of values in case none are passed
    if x_series is None:
        x_series = DataSchema["PCR_PRODUCT"]["field"]
    if y_series is None:
        # y_series = DataSchema["EXTRACTION_ID"]["field"]
        y_series = DataSchema["N_PRIMARY"]["field"]
    if colour_series is None:
        colour_series = DataSchema["EXP_ID"]["field"] + "_seqlib"
    
    #Filter the data so that there are no empty values
    df = combined_data.df
    #Slice the data to the three key columns
    dff = df[[x_series, y_series, colour_series]].copy(deep=True)
    #Drop in place
    dff.dropna(axis=0,how='any', inplace=True)
    dff.mask(dff.eq('None')).dropna(axis=0, how='any', inplace=True)
    
    print(f"Plotting x: {x_series}, y: {y_series}, colour: {colour_series}, df shape ={dff.shape}")                
    
    # Plot the values
    fig = px.scatter(dff, 
                    x=x_series,
                    y=y_series,
                    color=colour_series
                    )

    fig.update_yaxes(title=FieldLabels.get(y_series))
    fig.update_xaxes(title=FieldLabels.get(x_series))
    fig.update_layout(legend_title_text=FieldLabels.get(colour_series))

    
    return fig

def render(app: Dash, combined_data):
    
    @app.callback(
        Output(ids.SELECTABLE_SCATTER, "figure"),
        [Input(ids.COLUMN_DROPDOWN + "_1", "value"),
         Input(ids.COLUMN_DROPDOWN + "_2", "value"),
         Input(ids.COLUMN_DROPDOWN + "_3", "value"),
        ]
    )
    def update_scatter(dd1, dd2, dd3) -> px.scatter:
        fig = create_scatter(combined_data, x_series=dd1, y_series=dd2, colour_series=dd3)
        return fig

    #Build initial graph
    fig = create_scatter(combined_data)
    return html.Div(dcc.Graph(figure=fig, id=ids.SELECTABLE_SCATTER))

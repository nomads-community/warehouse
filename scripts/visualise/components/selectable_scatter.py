from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
from . import ids
from lib.dataschemas import ExpDataSchema, SeqDataSchema, DataSources

def create_scatter(df : pd.DataFrame, x_series = None, y_series = None, colour_series = None):

    #Define a default set of values in case none are passed
    if x_series is None:
        x_series = ExpDataSchema.PCR_PRODUCT_ngul
    if y_series is None:
        y_series = SeqDataSchema.N_PRIMARY
    if colour_series is None:
        colour_series = ExpDataSchema.EXP_ID + "_seqlib"

    print(f"Plotting x: {x_series}, y: {y_series}, colour: {colour_series}")    

    fig = px.scatter(df, 
                    x=x_series,
                    y=y_series,
                    color=colour_series
                    )
    
    fig.update_yaxes(title=DataSources.ALL_VARS_DICT.get(y_series))
    fig.update_xaxes(title=DataSources.ALL_VARS_DICT.get(x_series))
    fig.update_layout(legend_title_text=DataSources.ALL_VARS_DICT.get(colour_series))

    
    return fig

def render(app: Dash, alldata_df):
    
    @app.callback(
        Output(ids.SELECTABLE_SCATTER, "figure"),
        [Input(ids.COLUMN_DROPDOWN + "_1", "value"),
         Input(ids.COLUMN_DROPDOWN + "_2", "value"),
         Input(ids.COLUMN_DROPDOWN + "_3", "value"),
        ]
    )
    def update_scatter(dd1, dd2, dd3) -> px.scatter:
        fig = create_scatter(alldata_df, x_series=dd1, y_series=dd2, colour_series=dd3)
        return fig

    #Build initial graph
    fig = create_scatter(alldata_df)
    return html.Div(dcc.Graph(figure=fig, id=ids.SELECTABLE_SCATTER))

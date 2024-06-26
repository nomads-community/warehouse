from dash import Dash, html, dcc
from dash.dependencies import Output, Input
import plotly.express as px
import pandas as pd
from . import ids, colours
from lib.dataschemas import SeqDataSchema, DataSources

color_map = {
    SeqDataSchema.ALL_VARS_DICT.get(SeqDataSchema.N_UNMAPPED): colours.GREY,
    SeqDataSchema.ALL_VARS_DICT.get(SeqDataSchema.N_PRIMARY): colours.BLUE_DARK,
    SeqDataSchema.ALL_VARS_DICT.get(SeqDataSchema.N_SECONDARY): colours.BLUE_MEDIUM,
    SeqDataSchema.ALL_VARS_DICT.get(SeqDataSchema.N_CHIMERA): colours.BLUE_LIGHT,
}

def render(app: Dash, seq_df : pd.DataFrame) -> html.Div:
    SCALE_OPTIONS = ["Linear", "Log"]

    @app.callback(
        Output(ids.SEQ_OUTPUT, "figure"),
        Input(ids.SEQ_OUTPUT_SCALE_BUTTON, "n_clicks")
    )
    def update_chart(integer : int ) -> px.bar:
        if integer % 2 == 0:
            fig.update_yaxes(type="log")
            fig.update_yaxes(title="# Reads (log)")
        else:
            fig.update_yaxes(type="linear")
            fig.update_yaxes(title="# Reads")
        return fig  
    
    # Define column list for melting
    cols = SeqDataSchema.MAPPED_LIST + [SeqDataSchema.EXP_ID]

    #Melt and Group Data
    df_tmp = seq_df[cols].melt(id_vars=SeqDataSchema.EXP_ID, var_name="category", value_name="count")
    df = df_tmp.groupby([SeqDataSchema.EXP_ID, "category"])["count"].sum().reset_index()

    #Sort by Category into a custom order 
    df.sort_values(by="category", key=lambda col: col.map(SeqDataSchema.MAPPED_LIST.index), inplace=True)
    #Replace Category name to user friendly version
    df["category_label"] = df['category'].replace(DataSources.ALL_VARS_DICT)
    
    # Create the stacked bar graph
    fig = px.bar(
        df,
        x=SeqDataSchema.EXP_ID,
        y="count",
        color="category_label",
        color_discrete_map=color_map,
        barmode="stack",
    )

    # Customize plot
    fig.update_xaxes(title="Experiment ID")
    fig.update_layout(legend_title_text="Mapped Reads")

    return html.Div(
        children=[
            html.H2("Reads mapped by Experiment ID"),
            dcc.Graph(
                figure=fig, id=ids.SEQ_OUTPUT
            )
        ]
    )

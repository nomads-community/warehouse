from dash import Dash, html, dcc
from dash.dependencies import Output, Input
import plotly.express as px
from . import ids, colours

def render(app: Dash, seq_data : object) -> html.Div:
    """
    Creates a barchart of number of reads
    """
    #Pull out seq_data dataschema
    SeqDataSchema = seq_data.DataSchema
    
    #Define colour map
    colour_map = {SeqDataSchema.N_UNMAPPED[1]: colours.GREY, 
                  SeqDataSchema.N_PRIMARY[1]: colours.BLUE_DARK,
                  SeqDataSchema.N_SECONDARY[1]: colours.BLUE_MEDIUM,
                  SeqDataSchema.N_CHIMERA[1]: colours.BLUE_LIGHT,
                  }
    
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
    cols = SeqDataSchema.MAPPED_LIST + [ SeqDataSchema.EXP_ID[0]]
    
    #Melt and Group Data
    seq_df = seq_data.summary_bam
    df_tmp = seq_df[cols].melt(id_vars=SeqDataSchema.EXP_ID[0], var_name="category", value_name="count")
    df = df_tmp.groupby([SeqDataSchema.EXP_ID[0], "category"])["count"].sum().reset_index()
    
    #Sort by Category into a custom order 
    df.sort_values(by="category", key=lambda col: col.map(SeqDataSchema.MAPPED_LIST.index), inplace=True)
    #Replace Category name to user friendly version
    df["category_label"] = df['category'].replace(SeqDataSchema.field_labels)

    # Create the stacked bar graph
    fig = px.bar(
        df,
        x=SeqDataSchema.EXP_ID[0],
        y="count",
        color="category_label",
        color_discrete_map=colour_map,
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

from dash import Dash, html, dcc
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output

from warehouse.visualise.components import ids
from warehouse.lib.general import reformat_nested_dict
from warehouse.lib.dataframes import filtered_dataframe

charts=[ "Reads Mapped", "Amplicon Pass Rates", "Sample pass rate" ]

def render_qc_panel(app: Dash, sequence_data) -> html.Div:
    selections = selection_panel(app, sequence_data)
    chart = qc_chart(app, sequence_data)
    return html.Div(
        className="panel",
        children=[
            html.H2("Sequencing Overview:"),
            selections,
            chart
        ]
    )


def selection_panel(app: Dash, sequence_data) -> html.Div:
    
    SeqDataSchema = sequence_data.DataSchema
    #Generate a list of unique expt_ids
    expt_ids = sequence_data.qc_per_expt[SeqDataSchema.EXP_ID[0]].unique().tolist()
    
    @app.callback(
        Output(ids.SEQ_QC_EXPT_LIST, "value"),
        Input(ids.SEQ_SELECT_ALL_EXPTS_BUTTON, "n_clicks"),
        )
    def reset_expt_list(_: int) -> list[str]:
        return expt_ids
    
    @app.callback(
            Output(ids.SEQ_QC_SAMPLE_TYPE_SELECTOR, "children"),
            Output(ids.SEQ_QC_SAMPLE_TYPE_SELECTOR, "style"),
            Input(ids.SEQ_QC_SAMPLE_TYPE_SELECTOR, "n_clicks"),
            Input(ids.SEQ_QC_EXPT_CHART_TYPE, "value"),
    )
    def update_text_and_button_visibility(n_clicks: int, chart_type: str) -> str:
        # Update the text on the selection button
        if n_clicks % 2 == 0:
            sample_type="Filter to Samples"
        else:
            sample_type="Filter to Controls"
        # Update whether the button should be shown
        if chart_type != charts[1]:
            visible={'display': 'none'}
        else:
            visible={'display': 'block'}

        return sample_type, visible
    
    
    expts = expt_selections(expt_ids)
    chart_selection = dcc.Dropdown(
                id=ids.SEQ_QC_EXPT_CHART_TYPE,
                options=[{"label": id, "value": id} for id in charts],
                value=charts[0],
                multi=False,
            )
    sample_control = html.Button(
                children="Filter to Controls",
                id=ids.SEQ_QC_SAMPLE_TYPE_SELECTOR,
                n_clicks=0,
            )
    
    return html.Div(
        className="flex-row",
        children=[
            chart_selection,
            expts,
            sample_control
        ]
    )

def expt_selections(expt_ids) -> html.Div:
    return html.Div(
                className="flex-row",
                children=[
                    html.Button(
                        className="dropdown-button",
                        children=["Select all experiments"],
                        id=ids.SEQ_SELECT_ALL_EXPTS_BUTTON,
                        n_clicks=0,
                    ),
                    dcc.Dropdown(
                        className="dropdown-fill",
                        id=ids.SEQ_QC_EXPT_LIST,
                        options=[{"label": id, "value": id} for id in expt_ids],
                        value=expt_ids,
                        multi=True,
                    ),
                ]
            )

def qc_chart(app: Dash, sequence_data):
    # Define df and schema to use from object
    SeqDataSchema = sequence_data.DataSchema
    qc_per_expt_df = sequence_data.qc_per_expt
    qc_per_sample_df = sequence_data.qc_per_sample
    qc_reads_mapped = sequence_data.summary_bam

    @app.callback(
        Output(ids.SEQ_QC_EXPT_CHART, "children"),
        [
            Input(ids.SEQ_QC_EXPT_LIST, "value"),
            Input(ids.SEQ_QC_EXPT_CHART_TYPE, "value"),
            Input(ids.SEQ_QC_SAMPLE_TYPE_SELECTOR, "n_clicks")
            ],
    )
    def filter_sample_type(expt_ids: list[str], chart_type: str, n_clicks: int) -> html.Div:
        #Filters the entries to samples or controls as relevent
        if n_clicks % 2 == 0:
            samples=True
        else:
            samples=False
        
        if chart_type==charts[1]:
            df=filtered_dataframe(qc_per_sample_df, SeqDataSchema.EXP_ID[0], expt_ids)
            fig=fig_amplicon_pass_coverage(df, SeqDataSchema, sample=samples)
        elif chart_type==charts[2]:
            df=filtered_dataframe(qc_per_expt_df, SeqDataSchema.EXP_ID[0], expt_ids)
            fig=fig_qc_by_exptid(df, SeqDataSchema)
        else:
            df=filtered_dataframe(qc_reads_mapped, SeqDataSchema.EXP_ID[0], expt_ids)
            fig=fig_reads_mapped(df, SeqDataSchema)
        
        if df.empty:
            return html.Div("No data selected.", id="1")                   
    
        return html.Div(dcc.Graph(figure=fig), id=ids.SEQ_QC_EXPT_CHART)

    return html.Div(id=ids.SEQ_QC_EXPT_CHART)


def fig_amplicon_pass_coverage (df : pd.DataFrame, SeqDataSchema,
                                      percent: bool = True, 
                                      sample: bool = True) -> px.bar:
    """
    Generates a figure of the percentage of amplicons passing a threshold coverage for
    each sample in an expt

    Args:
        df (pd.DataFrame): Dataframe of per sample amplicon outputs
        percent (bool): Output y axis as a percentage of samples in expt or raw count
        sample (bool): Filter dataframe for samples or controls

    Returns:
        fig: A px.bar of the data
    """
    #Filter the df to samples or not samples
    if sample:
        df_f = df[df[SeqDataSchema.SAMPLE_TYPE[0]]=='sample']
    else:
        df_f = df[df[SeqDataSchema.SAMPLE_TYPE[0]]!='sample']
    df = df_f.copy()
    
    #Calulate the %age passing
    df['amp_pass']= df[SeqDataSchema.N_AMPLICONSPASSCOV[0]] / df[SeqDataSchema.N_AMPLICONS[0]]
    
    # Define bin edges and colours
    bins = [-1, 0.2, 0.4, 0.6, 0.8, 1.0]
    bin_labels = ['<20', '20-40', '40-60', '60-80', '>80']
    bin_colours = ['crimson', 'tomato', 'gold', 'forestgreen', '#036B52']
    
    #Apply bins to df
    df['bins'] = pd.cut(df['amp_pass'], bins=bins, labels=bin_labels)

    # Calculate counts per exptid
    counts_per_exp = df.groupby([SeqDataSchema.EXP_ID[0]], observed=False)[SeqDataSchema.BARCODE[0]].count().reset_index()
    counts_per_exp = counts_per_exp.rename(columns={SeqDataSchema.BARCODE[0]: 'total'})
    
    #Calculate counts per bin per exptid
    df_group = df.groupby([SeqDataSchema.EXP_ID[0],'bins'], observed=False)[SeqDataSchema.BARCODE[0]].count().reset_index()
    df_group = df_group.rename(columns={SeqDataSchema.BARCODE[0]: 'count','bins': 'amplicons_pass'})
    
    #Merge two df and calculate percentage
    final_df = pd.merge(left=df_group, right=counts_per_exp, on=SeqDataSchema.EXP_ID[0], how='outer')
    final_df['percent_passed'] = (final_df['count']/final_df['total']) * 100
    
    #Define y axis
    if percent:
        y_col = 'percent_passed'
    else:
        y_col = 'count'
    
    fig = px.bar(final_df, 
                 x=SeqDataSchema.EXP_ID[0], 
                 y=y_col, 
                 color='amplicons_pass', 
                 color_discrete_sequence=bin_colours,
                 labels={SeqDataSchema.EXP_ID[0]: SeqDataSchema.EXP_ID[1],
                         'percent_passed': 'No. samples (%)', 
                         'count': 'Number samples',
                         'amplicons_pass': SeqDataSchema.N_AMPLICONSPASSCOV[1]}
                )
    return fig

def fig_qc_by_exptid (df : pd.DataFrame, SeqDataSchema, y_axis: str = "test") -> px.bar:
    """
    Generates a figure of the percentage of samples succesfully sequenced in each expt

    Args:
        df (pd.DataFrame): Dataframe of per experiment qc
        SeqDataSchema (object): 
    Returns:
        fig: A px.bar of the data
    """
    #TO DO
    #Filter the df to samples or not samples
   
    #Define metrics for figure
    labels= reformat_nested_dict(SeqDataSchema.dataschema_dict, 'field', 'label')
    x=SeqDataSchema.EXP_ID[0]
    y=SeqDataSchema.PERCENT_PASSED_EXC_NEG_CTRL[0]
    # y=SeqDataSchema.f"{y_axis}"

    colour_map = {
        True : "green",
        False: "red" ,
    }
    
    #Generate the figure
    fig=px.bar(df, x=x, y=y, labels=labels, 
               color='expt_pass', color_discrete_map=colour_map)
    
    # Set the y-axis maximum and add a horizontal line
    fig.update_layout(
        yaxis=dict(range=[0, 100]),
        shapes=[dict(
                type="line",
                x0=0,
                x1=1,
                y0=60,
                y1=60,
                xref="paper",
                yref="y",
                line=dict(color="green", width=2, dash="dash")
                )]
        )
    
    return fig

def fig_reads_mapped(df : pd.DataFrame, SeqDataSchema) -> px.bar:
    """
    Creates a barchart of number of reads
    """

    # Define colour map
    colour_map = {
        SeqDataSchema.N_PRIMARY[1]: "#0037FF" ,
        SeqDataSchema.N_SECONDARY[1]: "#4285F4",
        SeqDataSchema.N_CHIMERA[1]: "#90CAF9",
        SeqDataSchema.N_UNMAPPED[1]: "grey",
    }

    # Define column list for melting
    cols = SeqDataSchema.READS_MAPPED_TYPE + [SeqDataSchema.EXP_ID[0]]

    # Melt and Group Data
    df_tmp = df[cols].melt(
        id_vars=SeqDataSchema.EXP_ID[0], var_name="category", value_name="count"
    )
    df = (
        df_tmp.groupby([SeqDataSchema.EXP_ID[0], "category"])["count"]
        .sum()
        .reset_index()
    )

    # Sort by Category into a custom order
    df.sort_values(
        by="category",
        key=lambda col: col.map(SeqDataSchema.READS_MAPPED_TYPE.index),
        inplace=True,
    )
    # Replace Category name to user friendly version
    df["category_label"] = df["category"].replace(SeqDataSchema.field_labels)

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

    #Generate the scale_switcher
    # switcher = qc_reads_switcher(app)
    return fig


def panel_reads_mapped(app, df : pd.DataFrame, SeqDataSchema) -> html.Div:
    """
    Creates a panel of a barchart and scale selector
    """
    @app.callback(
        Output(ids.SEQ_READSMAPPED_SCALE_BTN, "children"),
        #Output(ids.SEQ_QC_EXPT_CHART, "figure"),
        Input(ids.SEQ_READSMAPPED_SCALE_BTN, "n_clicks"),
    )
    def update_scale_and_text(n_clicks: int) -> str :
        print(f"n_clicks: {n_clicks}")
        if n_clicks % 2 == 0:
            # fig.update_yaxes(type="log")
            # fig.update_yaxes(title="# Reads (log)")
            return "Linear" #, fig
        # fig.update_yaxes(type="linear")
        # fig.update_yaxes(title="# Reads")
        return "Log" #, fig

    # Define colour map
    colour_map = {
        SeqDataSchema.N_PRIMARY[1]: "#0037FF" ,
        SeqDataSchema.N_SECONDARY[1]: "#4285F4",
        SeqDataSchema.N_CHIMERA[1]: "#90CAF9",
        SeqDataSchema.N_UNMAPPED[1]: "grey",
    }

    # Define column list for melting
    cols = SeqDataSchema.READS_MAPPED_TYPE + [SeqDataSchema.EXP_ID[0]]

    # Melt and Group Data
    df_tmp = df[cols].melt(
        id_vars=SeqDataSchema.EXP_ID[0], var_name="category", value_name="count"
    )
    df = (
        df_tmp.groupby([SeqDataSchema.EXP_ID[0], "category"])["count"]
        .sum()
        .reset_index()
    )

    # Sort by Category into a custom order
    df.sort_values(
        by="category",
        key=lambda col: col.map(SeqDataSchema.READS_MAPPED_TYPE.index),
        inplace=True,
    )
    # Replace Category name to user friendly version
    df["category_label"] = df["category"].replace(SeqDataSchema.field_labels)

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
    figure = html.Div(dcc.Graph(figure=fig), id=ids.SEQ_QC_EXPT_CHART)
    
    #Generate the scale_switcher
    switcher = html.Button(
        children="Log",
        id=ids.SEQ_READSMAPPED_SCALE_BTN,
        n_clicks=0,
    )

    return html.Div(
        children=[figure,switcher])
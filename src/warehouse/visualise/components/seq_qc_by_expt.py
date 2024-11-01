from dash import Dash, html, dcc
import pandas as pd
import numpy as np
import plotly.express as px
from dash.dependencies import Input, Output

from warehouse.visualise.components import ids
from warehouse.lib.general import reformat_nested_dict
from warehouse.lib.dataframes import filtered_dataframe

#List of different charts that can be shown to the user based on their selection
charts=[ "Reads Mapped", "Amplicon Pass Rates", "Sample pass rate" ]

def render(app: Dash, sequence_data) -> html.Div:
    selections = main_selection_panel(app, sequence_data)
    chart = qc_chart(app, sequence_data)
    chart_selections= select_sample_type(app)
    scale = switch_y_axis_scale(app)
    plot = switch_percent_num(app)
    return html.Div(
        className="panel",
        children=[
            html.H2("Sequencing Overview:"),
            selections,
            chart,
            chart_selections,
            scale,
            plot
        ]
    )


def main_selection_panel(app: Dash, sequence_data) -> html.Div:
    """
    Provides an html.Div container that has the universal options for the user to select

    Requires:
        app (Dash) : Dash app for callbacks
        sequence_data(Object) : Object with all seq data

    Returns:
        html.Div

    """
    #Pull out the data schema for labels etc
    SeqDataSchema = sequence_data.DataSchema
    #Generate a list of unique expt_ids
    expt_ids = sequence_data.qc_per_expt[SeqDataSchema.EXP_ID[0]].unique().tolist()
    
    @app.callback(
        Output(ids.SEQ_QC_EXPT_LIST, "value"),
        Input(ids.SEQ_SELECT_ALL_EXPTS_BUTTON, "n_clicks"),
        )
    def reset_expt_list(_: int) -> list[str]:
        return expt_ids
    
    
    #Get expt selection panel
    expts = expt_selections(expt_ids)
    chart_selection = dcc.Dropdown(
                id=ids.SEQ_QC_EXPT_CHART_TYPE,
                options=[{"label": id, "value": id} for id in charts],
                value=charts[0],
                multi=False,
            )
    
    
    return html.Div(
        className="flex-row",
        children=[
            chart_selection,
            expts
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

    #Update the chart
    @app.callback(
        Output(ids.SEQ_QC_EXPT_CHART, "children"),
        [
            Input(ids.SEQ_QC_EXPT_LIST, "value"),
            Input(ids.SEQ_QC_EXPT_CHART_TYPE, "value"),
            Input(ids.SEQ_QC_SAMPLE_TYPE_SELECTOR, "n_clicks"),
            Input(ids.SEQ_QC_SCALE_BUTTON, "n_clicks"),
            Input(ids.SEQ_QC_PCT_NUM_BUTTON, "n_clicks"),
            ],
    )
    def update_chart(expt_ids: list[str], 
                     chart_type: str, 
                     type_clicks: int, 
                     scale_clicks: int,
                     pct_num_clicks: int) -> html.Div:
        #Filter to field samples or controls
        field = type_clicks % 2 == 0

        # Update scale from linear to log
        y_linear = scale_clicks % 2 == 0

        #Select whether to show percent or count on y axis
        pct_num = pct_num_clicks % 2 == 0
        
        #Generate the chart
        if chart_type==charts[1]:
            df=filtered_dataframe(qc_per_sample_df, SeqDataSchema.EXP_ID[0], expt_ids)
            fig=fig_amplicon_pass_coverage(df, SeqDataSchema, field=field, percent=pct_num)
        elif chart_type==charts[2]:
            df=filtered_dataframe(qc_per_expt_df, SeqDataSchema.EXP_ID[0], expt_ids)
            fig=fig_qc_by_exptid(df, SeqDataSchema)
        else:
            df=filtered_dataframe(qc_reads_mapped, SeqDataSchema.EXP_ID[0], expt_ids)
            fig=fig_reads_mapped(df, SeqDataSchema, y_linear=y_linear)
            
        if df.empty:
            return html.Div("No data selected.")
        
        return dcc.Graph(figure=fig)

    return html.Div(id=ids.SEQ_QC_EXPT_CHART)


def fig_amplicon_pass_coverage (df : pd.DataFrame, SeqDataSchema,
                                      percent: bool = True, 
                                      field: bool = True) -> px.bar:
    """
    Generates a figure of the percentage of amplicons passing a threshold coverage for
    each sample in an expt

    Args:
        df (pd.DataFrame): Dataframe of per sample amplicon outputs
        percent (bool): Output y axis as a percentage of samples in expt or raw count
        field (bool): Filter dataframe for samples or controls

    Returns:
        fig: A px.bar of the data
    """
    #Filter the df to samples or not samples
    if field:
        df_f = df[df[SeqDataSchema.SAMPLE_TYPE[0]]=='Field']
    else:
        df_f = df[df[SeqDataSchema.SAMPLE_TYPE[0]]!='Field']
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
    y_col = 'percent_passed' if percent else 'count'
    
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

def fig_qc_by_exptid (df : pd.DataFrame, SeqDataSchema) -> px.bar:
    """
    Generates a figure of the percentage of samples succesfully sequenced in each expt

    Args:
        df (pd.DataFrame): Dataframe of per experiment qc
        SeqDataSchema (object): 
    Returns:
        fig: A px.bar of the data
    """

    #Define metrics for figure
    labels= reformat_nested_dict(SeqDataSchema.dataschema_dict, 'field', 'label')
    x=SeqDataSchema.EXP_ID[0]
    y=SeqDataSchema.PERCENT_PASSED_EXC_NEG_CTRL[0]
    threshold=60

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
                y0=threshold,
                y1=threshold,
                xref="paper",
                yref="y",
                line=dict(color="green", width=2, dash="dash")
                )]
        )
    
    return fig

def fig_reads_mapped(df : pd.DataFrame, SeqDataSchema, y_linear: bool) -> px.bar:
    """
    Creates a barchart of number of mapped reads by type

    Args:
        df (pd.DataFrame): Dataframe of per experiment qc
        SeqDataSchema (object): Dataschema
        y_linear (bool): Plot linear or log y-axis
    Returns:
        fig: A px.bar of the data
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

    # Generate log in df and plot on y as needed
    df['count_log'] = np.log10(df['count'])
    y = 'count' if y_linear else 'count_log'
    ytitle = 'Reads' if y_linear else 'Reads (log)'
    
    # Create the stacked bar graph
    fig = px.bar(
        df,
        x=SeqDataSchema.EXP_ID[0],
        y=y,
        color="category_label",
        color_discrete_map=colour_map,
        barmode="stack"
    )

    # Customize plot
    fig.update_xaxes(title="Experiment ID")
    fig.update_yaxes(title=ytitle)
    fig.update_layout(legend_title_text="Mapped Reads")

    return fig


def select_sample_type(app) -> html.Button:
    @app.callback(
        [Output(ids.SEQ_QC_SAMPLE_TYPE_SELECTOR, "style"),
         Output(ids.SEQ_QC_SAMPLE_TYPE_SELECTOR, "children")],
        [Input(ids.SEQ_QC_EXPT_CHART_TYPE, "value"),
         Input(ids.SEQ_QC_SAMPLE_TYPE_SELECTOR, "n_clicks")]
        )
    def update_text_and_visibility(chart_type, n_clicks):
        # Update the text on the selection button
        btn_text="Filter to Controls" if n_clicks % 2 == 0 else "Filter to Field Samples"
        # And visibility
        visible={'display': 'block'} if chart_type in charts[1] else {'display': 'none'} 
        return visible, btn_text

    button = html.Button(
        children="Filter to Controls",
        id=ids.SEQ_QC_SAMPLE_TYPE_SELECTOR,
        n_clicks=0,
    )
    return button

def switch_y_axis_scale(app) -> html.Button:
    @app.callback(
        [Output(ids.SEQ_QC_SCALE_BUTTON, "style"),
         Output(ids.SEQ_QC_SCALE_BUTTON, "children")],
        [Input(ids.SEQ_QC_EXPT_CHART_TYPE, "value"),
         Input(ids.SEQ_QC_SCALE_BUTTON, "n_clicks")]
        )
    def update_text_and_visibility(chart_type, n_clicks):
        # Update the text on the selection button
        btn_text="Change to log y-axis" if n_clicks % 2 == 0 else "Change to linear y-axis"
        # And the visibility
        visible={'display': 'block'} if chart_type == charts[0] else {'display': 'none'}
        return visible, btn_text

    button = html.Button(
        children="Change to Log y-axis",
        id=ids.SEQ_QC_SCALE_BUTTON,
        n_clicks=0,
    )
    return button

def switch_percent_num(app) -> html.Button:
    @app.callback(
        [Output(ids.SEQ_QC_PCT_NUM_BUTTON, "style"),
         Output(ids.SEQ_QC_PCT_NUM_BUTTON, "children")],
        [Input(ids.SEQ_QC_EXPT_CHART_TYPE, "value"),
         Input(ids.SEQ_QC_PCT_NUM_BUTTON, "n_clicks")]
        )
    def update_text_and_visibility(chart_type, n_clicks):
        # Update the text on the selection button
        btn_text="Change to sample count on y_axis" if n_clicks % 2 == 0 else "Change to percent on y_axis"
        # And the visibility
        visible={'display': 'block'} if chart_type == charts[1] else {'display': 'none'}
        return visible, btn_text

    button = html.Button(
        children="Change to count on y_axis",
        id=ids.SEQ_QC_PCT_NUM_BUTTON,
        n_clicks=0,
    )
    return button

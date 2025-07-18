import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html

from warehouse.metadata.metadata import (
    ExpDataParser,
    ExpThroughputDataScheme,
    SampleMetadataParser,
)
from warehouse.visualise.components import ids


def render(
    app: Dash, sample_data: SampleMetadataParser, experiment_data: ExpDataParser
) -> html.Div:
    """
    Render the pie charts for experiment throughput.
    Args:
        app (Dash): The Dash app instance.
        sample_data (SampleMetadataParser): An instance containing sample metadata.
        experiment_data (ExpMetadataParser): An instance containing experiment metadata.
    Returns:
        html.Div: The layout containing the pie charts.
    """
    # Generate summary table
    df = summarise_exp_throughput(sample_data, experiment_data)

    # Pull in other values / variables
    values_cols = [
        ExpThroughputDataScheme.SAMPLES,
        ExpThroughputDataScheme.RXNS,
        ExpThroughputDataScheme.EXPTS,
    ]
    triptych = []

    # Generate the figs
    for values_col in values_cols:
        fig = generate_fig(df.copy(), values_col)
        triptych.append(fig)

    # Create a layout with three dcc.Graph elements
    layout = html.Div(
        className="panel",
        children=[
            html.H2("Throughput:"),
            html.Div(
                className="row-flex",
                children=[
                    dcc.Graph(
                        figure=fig,
                        id=f"{ids.TRYPTICH}_{col}",
                        style={
                            "width": "30%",
                            "display": "inline-block",
                            "verticalAlign": "top",
                        },
                    )
                    for col, fig in zip(values_cols, triptych)
                ],
            ),
        ],
    )

    return layout


def generate_fig(df, values_col):
    """
    Generate a pie chart figure based on the provided DataFrame and values column.
    Args:
        df (pd.DataFrame): DataFrame containing the data for the pie chart.
        values_col (str): The column name in the DataFrame to use for pie chart values.
    Returns:
        plotly.graph_objects.Figure: The generated pie chart figure.
    """
    names_col = "Experiment Type"
    colours_col = "colours"

    # Calculate the total
    total = df[values_col].sum().astype(int).astype(str)

    # Create fig
    fig = px.pie(df, values=values_col, names=names_col, hole=0.4)

    # Add a title
    fig.update_layout(
        title={"text": values_col.capitalize(), "x": 0.5, "xanchor": "center"},
    )

    # Change annotations and wedge order
    fig.update_layout(annotations=[dict(text=total, font_size=20, showarrow=False)])

    fig.update_traces(
        textinfo="value",
        marker_colors=df[colours_col],
        sort=False,
        direction="clockwise",
    )
    return fig


def summarise_exp_throughput(
    sample_data: object, experiment_data: object
) -> pd.DataFrame:
    """
    Summarizes the throughput of an experiment based on sample and experiment data.

    Args:
        sample_data (object): An instance of a class containing sample data.
        experiment_data (object): An instance of a class containing experiment data.

    Returns:
        dict: A dictionary containing summary counts
    """

    # Define colours
    colours = ["black", "yellow", "orange", "green"]
    # Define key fields
    SampleDataSchema = sample_data.DataSchema
    ExpDataSchema = experiment_data.dataschema

    # Create summaries of number of experiments and rxn performed
    exp_counts = (
        experiment_data.expts_df[ExpDataSchema.EXP_TYPE[0]]
        .value_counts()
        .rename("experiments")
    )
    rxn_counts = (
        experiment_data.rxns_df[ExpDataSchema.EXP_TYPE[0]]
        .value_counts()
        .rename("reactions")
    )

    sample_counts = (
        sample_data.df_with_exp[SampleDataSchema.STATUS[0]]
        .value_counts()
        .rename("samples")
    )
    colour_series = pd.Series(colours, index=ExpThroughputDataScheme.EXP_TYPES).rename(
        "colours"
    )

    # na cause the datatype to change to a float so combine all ints and change to int
    summary_counts_df = pd.concat(
        [sample_counts, exp_counts, rxn_counts, colour_series], axis=1
    )
    # Reindex so the order is the same as the types, so plots will be from least -> sequenced
    temp = summary_counts_df.reindex(ExpThroughputDataScheme.EXP_TYPES)
    temp.index.name = "Experiment Type"
    # Add in the colours and index as column
    summary_counts_df = temp.reset_index()

    return summary_counts_df

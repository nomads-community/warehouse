from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
from warehouse.visualise.components import ids
from warehouse.metadata.metadata import ExpThroughputDataScheme


def render(app: Dash, sample_data, experiment_data):
    # Generate summary table
    df = summarise_exp_throughput(sample_data, experiment_data)

    # Pull in other values / variables
    values_cols = [
        ExpThroughputDataScheme.EXPERIMENTS,
        ExpThroughputDataScheme.REACTIONS,
        ExpThroughputDataScheme.SAMPLES,
    ]
    triptych = []

    # Generate the figs
    for values_col in values_cols:
        fig = generate_fig(df.copy(), values_col)
        triptych.append(fig)

    # Create a layout with three dcc.Graph elements
    layout = html.Div(
        [
            dcc.Graph(figure=fig, id=f"{ids.TRYPTICH}_{col}")
            for col, fig in zip(values_cols, triptych)
        ],
        style={
            "display": "flex",
            "flex-direction": "row",
            "justify-content": "space-evenly",
        },
    )
    return layout


def generate_fig(df, values_col):
    names_col = "Experiment Type"
    colours_col = "colours"

    # Calculate the total
    total = df[values_col].sum().astype(int).astype(str)

    # Create fig
    fig = px.pie(df, values=values_col, names=names_col, hole=0.4)

    # Add a title
    fig.update_layout(
        title={"text": values_col.capitalize(), "x": 0.5, "xanchor": "center"}
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
    ExpDataSchema = experiment_data.DataSchema

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
        sample_data.df[SampleDataSchema.STATUS[0]].value_counts().rename("samples")
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

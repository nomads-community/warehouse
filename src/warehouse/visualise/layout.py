from dash import Dash, html

from warehouse.metadata.metadata import (
    Combine_Exp_Seq_Sample_data,
    ExpMetadataParser,
    SampleMetadataParser,
    SequencingMetadataParser,
)

from .components import (
    banner,
    pie_expt_types,
    selectable_scatter,
    seq_qc_by_expt,
    upset_plot,
)


def create_layout(
    app: Dash,
    sample_data: SampleMetadataParser,
    experiment_data: ExpMetadataParser,
    sequence_data: SequencingMetadataParser,
    combined_data: Combine_Exp_Seq_Sample_data,
    cli_flags,
) -> html.Div:
    """
    Return the webpage
    """

    return html.Div(
        className="entire",
        children=[
            banner.render(app, cli_flags),
            pie_expt_types.render(app, sample_data, experiment_data),
            seq_qc_by_expt.render(app, sequence_data, experiment_data),
            upset_plot.render(app, sequence_data, combined_data),
            selectable_scatter.render(app, combined_data),
        ],
    )

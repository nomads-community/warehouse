import logging
from pathlib import Path

from dash import Dash

from warehouse.lib.logging import divider
from warehouse.metadata.metadata import (
    Combine_Exp_Seq_Sample_data,
    ExpDataMerge,
    SampleMetadataParser,
    SequencingMetadataParser,
)
from warehouse.visualise.layout import create_layout

CSS_STYLE = ["scripts/visualise/assets/calling-style.css"]

# Define logging process
log = logging.getLogger(Path(__file__).stem)


def visualise(
    exp_data: ExpDataMerge,
    sample_data: SampleMetadataParser,
    seq_data: SequencingMetadataParser,
    combined_data: Combine_Exp_Seq_Sample_data,
):
    log.info(divider)
    log.info("Starting the warehouse dashboard")
    log.info(divider)

    app = Dash(__name__, external_stylesheets=CSS_STYLE)
    app.title = "Warehouse"
    app.layout = create_layout(app, sample_data, exp_data, seq_data, combined_data)
    app.run()

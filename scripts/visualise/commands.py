import click
from pathlib import Path
from dash import Dash
import pandas as pd
from lib.dataschemas import ExpDataSchema, SampleDataSchema, SeqDataSchema
from lib.general import check_file_present, Regex_patterns, identify_files_by_search
from lib.controls import load_controls
from metadata.metadata import ExpMetadataMerge, SampleMetadataParser, SequencingMetadataParser
from .layout import create_layout
CSS_STYLE=["scripts/visualise/assets/calling-style.css"]

@click.command(short_help="Dashboard to visualise summary data from NOMADS assays")

@click.option(
    "-e",
    "--exp_folder",
    type=Path,
    required=True,
    help="Path to folder containing completed experimental Excel template files."
)

@click.option(
    "-s",
    "--seq_folder",
    type=Path,
    required=True,
    help="Path to folder containing outputs from Nomadic / Savannah."
)

@click.option(
    "-c",
    "--sample_csv",
    type=Path,
    required=True,
    help="Path to csv file containing sample metadata information."
)

def visualise(exp_folder : Path, sample_csv : Path = None, seq_folder : Path = None ):
    
    print("Loading controls data")
    controls = load_controls()
    print("="*80)
    
    print("Extracting experimental data")
    exp_fns = identify_files_by_search(exp_folder, Regex_patterns.NOMADS_EXP_TEMPLATE, recursive=True)
    expdata_class = ExpMetadataMerge(exp_fns)

    print("Extracting sample data")
    check_file_present(sample_csv)
    sampledata_class = SampleMetadataParser(sample_csv, expdata_class.rxns_df)
    print(f"   with {sampledata_class.df.shape[0]} entries")
    print("="*80)

    print("Extracting sequence summary data")
    sequencedata_class= SequencingMetadataParser(seq_folder, expdata_class.rxns_df)
    print("="*80)

    print("Combining data sources")
    # Add in the sequence data
    alldata_df = pd.merge(expdata_class.all_df, sequencedata_class.summary_bam, 
                        left_on=[ExpDataSchema.BARCODE, ExpDataSchema.EXP_ID + "_seqlib", ExpDataSchema.SAMPLE_ID],
                        right_on=[SeqDataSchema.BARCODE, SeqDataSchema.EXP_ID, SeqDataSchema.SAMPLE_ID],
                        how ="outer")
    # Add in the sample data 
    alldata_df = pd.merge(alldata_df, sampledata_class.df, 
                        left_on=[ExpDataSchema.SAMPLE_ID],
                        right_on=[SampleDataSchema.SAMPLE_ID],
                        how="outer")

    # OUTPUTS FOR NOTEBOOK ETC
    debug=False
    if debug:
        print("Exporting data for debugging")
        nb_folder = Path("./notebooks")
        expdata_class.swga_df.to_csv(nb_folder.joinpath("rxn_swga_df.csv"),index=False)
        expdata_class.pcr_df.to_csv(nb_folder.joinpath("rxn_pcr_df.csv"),index=False)
        expdata_class.seqlib_df.to_csv(nb_folder.joinpath("rxn_seqlib_df.csv"),index=False)
        expdata_class.rxns_df.to_csv(nb_folder.joinpath("rxns_df.csv"),index=False)
        expdata_class.expts_df.to_csv(nb_folder.joinpath("exps_df.csv"),index=False)
        expdata_class.all_df.to_csv(nb_folder.joinpath("exp_all_df.csv"),index=False)
        expdata_class.swga_df.to_csv(nb_folder.joinpath("swga_df.csv"),index=False)
        expdata_class.pcr_df.to_csv(nb_folder.joinpath("pcr_df.csv"),index=False)
        expdata_class.seqlib_df.to_csv(nb_folder.joinpath("seqlib_df.csv"),index=False)
        sampledata_class.df.to_csv(nb_folder.joinpath("samples_df.csv"),index=False)
        sequencedata_class.summary_bam.to_csv(nb_folder.joinpath("seq_bam.csv"),index=False)
        sequencedata_class.summary_bedcov.to_csv(nb_folder.joinpath("seq_bedcov.csv"),index=False)

    print("Starting the warehouse dashboard")
    app = Dash(__name__, external_stylesheets=CSS_STYLE)
    app.title = "Warehouse"
    app.layout = create_layout(app, sampledata_class, expdata_class, sequencedata_class, alldata_df)
    app.run()

    # Lists all attributes of class to make a list if they have been updated and don't
    # want to manually edit
    # print(SeqDataSchema.get_all_variables())

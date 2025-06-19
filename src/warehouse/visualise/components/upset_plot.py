import base64
import logging
import warnings
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import upsetplot as up
import yaml
from dash import Dash, Input, Output, dcc, html

from warehouse.metadata.metadata import (
    Combine_Exp_Seq_Sample_data,
    SequencingMetadataParser,
)
from warehouse.visualise.components import ids

# Get logging process
log = logging.getLogger("upset_panel")

script_dir = Path(__file__).parent.resolve()


def render(
    app: Dash,
    sequence_data: SequencingMetadataParser,
    combined_data: Combine_Exp_Seq_Sample_data,
) -> html.Div:
    """
    Render the upset plot and dropdown options
    Args:
        app (Dash): The Dash app instance.
        sequence_data (SequencingMetadataParser): An instance containing sequence data.
    Returns:
        html.Div: The layout containing the dropdown and plots
    """

    @app.callback(
        Output(ids.UPSET_PLOT_IMG, "src"),
        Input(ids.UPSET_DROPDOWN, "value"),
    )
    def update_upset(gene: str = "kelch13") -> str:
        upset_plot = upsetplot_img(
            variants_df=bcf_df,
            ids_passed_QC=amp_uids_pass_QC,
            target_gene=gene,
            drugres_dict=drugres_dict,
            id_col=amp_uid,
        )
        upset_img = base64_encode_plot(upset_plot)
        return "data:image/png;base64,{}".format(upset_img)

    # Load drug resistance details from YAML file
    drugres_path = script_dir.parent / "drug_resistance_mutations.yml"
    with open(drugres_path, "r") as f:
        drugres_dict = yaml.safe_load(f)

    # Define uid
    rxn_uid = "rxn_uid"  # expt_id_barcode e.g. SLJS034_barcode01
    amp_uid = "amplicon_uid"  # expt_id_barcode_gene e.g. SLJS034_barcode01_crt

    #####################
    # Determine the amplicons passing QC thresholds
    #####################
    # bcftools only contains non-ref alleles. Therefore need to know all amplicons per rxn
    # that have passed QC to identify those that came up as reference. Unfortunately QC
    # outputs are at the sample level in sequence_data.qc_per_sample_with_exp. Therefore
    # will start with all possible amplicons per sample_id rxn and then determine using
    # coverage cutoffs from sequence_data.summary_bedcov_with_exp
    # and contamination cutoff from sequence_data.qc_per_sample_with_exp

    # Pull in translation from amplicon to gene name
    gene_names_path = script_dir.parent / "gene_names.yml"
    with open(gene_names_path, "r") as f:
        gene_names = yaml.safe_load(f)

    # Get a list of all sample IDs that have been sequenced
    sample_ref_df = combined_data.sample_set.copy(deep=True)
    sample_ref_df[rxn_uid] = sample_ref_df["expt_id"] + "_" + sample_ref_df["barcode"]
    rxn_uids_samples = sample_ref_df[rxn_uid].unique()
    log.debug(f"{sample_ref_df.shape[0]} sample_ref_df entries")

    # Limit qc_ids to those passing contamination threshold:
    qc_df = sequence_data.qc_per_sample_with_exp.copy(deep=True)
    log.debug(f"{qc_df.shape[0]} qc_per_sample_with_exp entries")
    qc_df = qc_df[qc_df["sample_pass_contamination"]]
    log.debug(f"   {qc_df.shape[0]} pass contamination")
    # Add a new col with a unique rxn_uid
    qc_df[rxn_uid] = qc_df["expt_id"] + "_" + qc_df["barcode"]
    # Extract rxns passing contamination
    rxn_uids_pass_contam = set(qc_df[rxn_uid])

    # Get amplicons passing coverage threshold:
    bed_df = sequence_data.summary_bedcov_with_exp.copy(deep=True)
    log.debug(f"{bed_df.shape[0]} summary_bedcov_with_exp entries")
    # Translate the amplicon to the gene name
    bed_df["gene"] = bed_df["name"].replace(gene_names)
    # Add new cols with uid
    bed_df[rxn_uid] = bed_df["expt_id"] + "_" + bed_df["barcode"]
    bed_df[amp_uid] = bed_df["expt_id"] + "_" + bed_df["barcode"] + "_" + bed_df["gene"]
    # Filter those not passing contamination and coverage
    bed_df = bed_df[bed_df["mean_cov"] >= 50]
    log.debug(f"   {bed_df.shape[0]} have mean_cov >= 50")
    bed_df = bed_df[bed_df[rxn_uid].isin(rxn_uids_pass_contam)]
    log.debug(f"   {bed_df.shape[0]} are in the rxn_uids_pass_contam")
    bed_df = bed_df[bed_df[rxn_uid].isin(rxn_uids_samples)]
    log.debug(f"   {bed_df.shape[0]} are samples")
    amp_uids_pass_QC = set(bed_df[amp_uid])

    #####################
    # Prep the bcftools data
    #####################
    bcf_df = sequence_data.bcftools_samples_only.copy(deep=True)
    # Translate the amplicon to the gene name
    bcf_df["gene"] = bcf_df["amplicon"].replace(gene_names)
    # Select ONLY nonsynonymous (missense) mutations
    bcf_df = bcf_df[bcf_df["mut_type"].str.contains("missense", na=False)]
    # Make a unique reference for results from each gene reaction
    bcf_df[amp_uid] = bcf_df["expt_id"] + "_" + bcf_df["sample"] + "_" + bcf_df["gene"]
    # Filter to those passing QC
    bcf_df = bcf_df[bcf_df[amp_uid].isin(amp_uids_pass_QC)]

    # Generate the plot
    upset_plot = upsetplot_img(
        variants_df=bcf_df,
        ids_passed_QC=amp_uids_pass_QC,
        target_gene="kelch13",
        drugres_dict=drugres_dict,
        id_col=amp_uid,
    )
    upset_img = base64_encode_plot(upset_plot)

    # Create the dropdown bar
    # Get a list of all genes that appear
    dr_muts = ["crt", "dhps", "dhfr", "kelch13", "mdr1"]
    # sorted(sequence_data.summary_bedcov["name"].unique())
    dropdown_options = [{"label": gene, "value": gene} for gene in dr_muts]
    dropdown = dcc.Dropdown(
        id=ids.UPSET_DROPDOWN,
        options=dropdown_options,
        className="wide_dropdown",
        placeholder="Select a gene",
    )

    # Create the upset plot layout
    layout = html.Div(
        className="panel",
        children=[
            html.H2("Variant Analysis:"),
            dropdown,
            html.Img(
                id=ids.UPSET_PLOT_IMG, src="data:image/png;base64,{}".format(upset_img)
            ),
        ],
    )

    return layout


def upsetplot_img(
    variants_df: pd.DataFrame,
    ids_passed_QC: list,
    target_gene: str,
    drugres_dict: dict,
    id_col=str,
) -> plt.figure:
    """
    Generate an upset plot in a matplot figure based on the provided DataFrame and values column.
    Args:
        variants_df (pd.DataFrame): DataFrame containing all non-ref muatations from bcftools
        ids_passed_QC (list): All ids (gene / amplicon level) that have passed QC
        target_gene (str): Name of the gene to generate the plot for
        drugres_dict (dict): Dictionary of drug resistance mutations and combinations
        id_col (str): Colname for unique identifier in variants_df (gene / amplicon level)
    Returns:
        plt.figure: The generated upset plot as a matplotlib fig.
    """

    # Remove annoying futurewarning
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning)
        log.debug(
            f"Looking up {target_gene} in drugres_dict with id_col={id_col} and ids_passed_QC={len(ids_passed_QC)}"
        )
        # Extract the drug resistance details
        target = drugres_dict.get(target_gene)
        candidate = list(target.get("candidate", []))
        validated = list(target.get("validated", []))
        combinations = target.get("combinations", {})
        log.debug(
            f"{target} mutations= {candidate} (candidate), {validated} (validated)\n {combinations} (combinations)"
        )

        # Filter df to relevent gene and samples passing QC
        variants_df = variants_df[variants_df["gene"] == target_gene]

        # Pivot data to wide where each row is a sample and cols are mutations
        mutation_matrix = pd.crosstab(variants_df[id_col], variants_df["aa_change"])
        mutation_matrix = mutation_matrix.astype(bool)

        # Identify and add in all samples that do NOT have a mutation as a new category
        wt_cat = "WT"
        ids_nonref = variants_df[id_col].unique()
        ids_ref = [g for g in ids_passed_QC if target_gene in g and g not in ids_nonref]
        log.debug(
            f"Identified {len(ids_nonref)} non-ref entries, and generated {len(ids_ref)} WT for {target_gene}"
        )
        new_rows_df = pd.DataFrame(
            False, index=ids_ref, columns=mutation_matrix.columns
        )
        # Add in wt values if there are
        if ids_ref:
            mutation_matrix[wt_cat] = False
            new_rows_df[wt_cat] = True
            mutation_matrix = pd.concat([mutation_matrix, new_rows_df])

        # Turn into a multi-level index with counts
        upset_data = up.from_indicators(mutation_matrix)

        # Ensure that if there is only one category e.g. WT or every sample mutated at one locus
        if mutation_matrix.shape[1] == 1:
            fig = plt.figure(figsize=(0.5, 3))
            ax = fig.add_subplot(111)
            ax.text(
                0.5,
                0.5,
                f"All samples are {list(mutation_matrix.columns)[0]} for {target_gene} so unable to plot",
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax.transAxes,
            )
            ax.axis("off")
        else:
            # Create the upset object
            up_obj = up.UpSet(
                upset_data,
                subset_size="count",
                sort_by="cardinality",
                show_percentages="{:.0%}",
                show_counts=True,
            )
            ###################
            # Add colours
            ###################
            for colour, members in combinations.items():
                # Ensure all members present before adding colour
                members_set = set(members)
                present_set = set(mutation_matrix.columns)
                if members_set.issubset(present_set):
                    up_obj.style_subsets(present=members, facecolor=colour)
            # and wild-type
            if ids_ref:
                up_obj.style_subsets(present=wt_cat, facecolor="green")

            # Highlight candidate markers
            for c in candidate:
                if c in mutation_matrix.columns:
                    up_obj.style_categories(
                        c, shading_facecolor="lightgrey", shading_linewidth=1
                    )
                    up_obj.style_categories(
                        c,
                        bar_facecolor="tab:orange",
                        bar_hatch="xx",
                        bar_edgecolor="black",
                    )
            # Highlight validated markers
            for v in validated:
                if v in mutation_matrix.columns:
                    up_obj.style_categories(
                        v, shading_facecolor="darkgrey", shading_linewidth=1
                    )
                    up_obj.style_categories(
                        v,
                        bar_facecolor="tab:red",
                        bar_hatch="xx",
                        bar_edgecolor="black",
                    )

            # Create the figure explicitly and plot onto it
            fig = plt.figure(figsize=(6, 8))
            up_plot = up_obj.plot(fig=fig)

            # Formatting
            up_plot["intersections"].set_ylabel("Count")  # Intersections y-axis
            up_plot["totals"].set_xlabel("Count")  # Sets x-axis

        return fig


def base64_encode_plot(matplot: plt.figure) -> base64:
    buffer = BytesIO()
    matplot.savefig(buffer, format="png", bbox_inches="tight", dpi=150)
    buffer.seek(0)  # Rewind the buffer to the beginning

    # Encode the image to base64 for embedding in HTML
    encoded_image = base64.b64encode(buffer.read()).decode("utf-8")

    # Close the Matplotlib figure to free up memory
    plt.close(matplot)

    return encoded_image

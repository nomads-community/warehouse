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
        [Output(ids.UPSET_PLOT_IMG, "src"), Output(ids.UPSET_PLOT_MSG, "children")],
        [
            Input(ids.UPSET_DROPDOWN, "value"),
            Input(ids.SEQ_QC_EXPT_LIST, "value"),
        ],
    )
    def update_upset(gene: str, expt_ids: list[str]) -> str:
        # Entered gene is None, so use the default kelch13
        if gene is None:
            gene = target_gene

        # Limit to selected expt_ids
        temp = amp_uids_pass_QC_df[amp_uids_pass_QC_df["expt_id"].isin(expt_ids)]
        if temp.empty:
            # If no expt_ids selected, return empty plot and message
            log.warning("No valid sequence data identified, returning empty plot.")
            return ["", f"No sequencing data available for {gene}"]

        # Generate the upset plot
        upset_plot = upsetplot_fig(
            variants_df=bcf_df,
            ids_passed_QC=temp,
            gene=gene,
            muts_dict=muts_dict,
        )
        upset_img = base64_encode_plot(upset_plot)
        upset = "data:image/png;base64,{}".format(upset_img)
        msg = percentage_sequenced_msg(
            amp_uids_pass_QC_df, gene, combined_data.sample_set
        )
        return [upset, msg]

    muts_dict = create_mutations_dict()

    # Load data
    bcf_df = sequence_data.bcftools_samples_QC_pass.copy(deep=True)
    amp_uids_pass_QC_df = sequence_data.amp_uids_pass_QC.copy(deep=True)
    # Identify first gene in the list
    target_gene = list(muts_dict.keys())[0]

    # Generate the plot
    upset_plot = upsetplot_fig(
        variants_df=bcf_df,
        ids_passed_QC=amp_uids_pass_QC_df,
        gene=target_gene,
        muts_dict=muts_dict,
    )
    upset_img = base64_encode_plot(upset_plot)

    # Get a list of all genes and create dropdown
    genes = muts_dict.keys()
    dropdown_options = [{"label": gene, "value": gene} for gene in genes]
    dropdown = dcc.Dropdown(
        id=ids.UPSET_DROPDOWN,
        options=dropdown_options,
        className="dropdown-fill",
        placeholder="Select a gene",
    )

    msg = percentage_sequenced_msg(
        amp_uids_pass_QC_df, target_gene, combined_data.sample_set
    )
    info = "INFO: Individual mutations are shown in rows, with candidate (light grey / orange) and validated (dark grey / red) mutations highlighted. Combinations are shown vertically with known combinations highlighted in colour. Wild-type (WT) is shown in green."

    # Create the upset plot layout
    layout = html.Div(
        className="panel",
        children=[
            html.H2("Variant Analysis:"),
            html.Div(
                className="selection_and_info",
                children=[
                    dropdown,
                    html.P(info, className="info_text"),
                ],
            ),
            html.Img(
                id=ids.UPSET_PLOT_IMG,
                src="data:image/png;base64,{}".format(upset_img),
            ),
            html.P(id=ids.UPSET_PLOT_MSG, children=msg),
        ],
    )

    return layout


def upsetplot_fig(
    variants_df: pd.DataFrame,
    ids_passed_QC: pd.DataFrame,
    gene: str,
    muts_dict: dict,
) -> plt.Figure:
    """
    Generate an upset plot in a matplot figure based on the provided DataFrame and values column.
    Args:
        variants_df (pd.DataFrame): DataFrame containing all non-ref mutations
        ids_passed_QC (pd.DataFrame): All ids (gene / amplicon level) that have passed QC
        target_gene (str): Name of the gene to generate the plot for
        muts_dict (dict): Dictionary of mutations and combinations
        ax (plt.Axes): Optional. The matplotlib Axes object to plot on.
                    If None, a new figure and axes will be created.
    Returns:
        plt.Figure: The generated upset plot as a matplotlib fig.
    """

    # Remove annoying futurewarning
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning)
        log.debug(
            f"Looking up {gene} in drugres_dict with ids_passed_QC={len(ids_passed_QC)}"
        )
        # Extract the mutation details
        target = muts_dict.get(gene)
        candidate = list(target.get("candidate", []))
        validated = list(target.get("validated", []))
        combinations = target.get("combinations", {})
        log.debug(
            f"{target} mutations= {candidate} (candidate), {validated} (validated)\n {combinations} (combinations)"
        )
        # Filter variants to relevant gene
        variants_df = variants_df[variants_df["gene"] == gene]

        # Pivot data to wide where each row is a sample and cols are mutations
        mutation_matrix = pd.crosstab(
            variants_df["sample_id"], variants_df["aa_change"]
        )
        mutation_matrix = mutation_matrix.astype(bool)

        # Identify all entries that do NOT have a mutation
        ids_nonref = list(variants_df["sample_id"].unique())
        ids_ref = ids_passed_QC[
            (ids_passed_QC["gene"].isin([gene]))
            & ~(ids_passed_QC["sample_id"].isin(ids_nonref))
        ]
        log.debug(
            f"Identified {len(ids_nonref)} non-ref entries, and generated {len(ids_ref)} WT entries for {gene}"
        )

        # Add in wt values if there are
        wt_cat = "WT"
        if not ids_ref.empty:
            new_rows_df = pd.DataFrame(
                False, index=ids_ref["sample_id"], columns=mutation_matrix.columns
            )
            mutation_matrix[wt_cat] = False
            new_rows_df[wt_cat] = True
            mutation_matrix = pd.concat([mutation_matrix, new_rows_df])

        # Deal with empty or single category (all WT or all mutated) matrix
        if mutation_matrix.empty or mutation_matrix.shape[1] == 1:
            if mutation_matrix.empty:
                text_msg = "No data available."
            else:
                text_msg = f"All samples are {list(mutation_matrix.columns)[0]} for {gene} so unable to plot"

            log.warning(text_msg)

            fig = plt.figure(figsize=(0.5, 3))
            ax = fig.add_subplot(111)
            ax.text(
                0.5,
                0.5,
                text_msg,
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax.transAxes,
            )
            ax.axis("off")
            return fig

        # Turn into a multi-level index with counts
        upset_data = up.from_indicators(mutation_matrix)

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
        if not ids_ref.empty:
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
        # Add plot to figure
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


def percentage_sequenced_msg(
    amp_uids_pass_QC_df: pd.DataFrame,
    gene: str,
    amp_uids_attempted_df: pd.DataFrame,
) -> str:
    """
    Determine the percentage of samples that have been sequenced
    Args:
        amp_uids_pass_QC_df (pd.Dataframe): Amplicon df that passed QC
        gene(str): Name of gene to filter to
        amp_uids_attempted_df (pd.Dataframe): Amplicon df of all sequenced
    Returns:
        str: Summary message for user feedback
    """
    # Calculate all amplicons that have passed QC for the target gene and count
    passed = amp_uids_pass_QC_df[amp_uids_pass_QC_df["gene"] == gene]
    num_seq = passed["sample_id"].nunique()

    # Count number attempted. Note that this assumes different panels were NOT used
    # on different samples, which will almost always be true
    num_attempted = amp_uids_attempted_df["sample_id"].nunique()
    if num_attempted == 0:
        msg = f"No samples attempted sequencing for {gene}. "
    else:
        # Calculate percentage
        if num_seq == 0:
            msg = f"No samples successfully sequenced for {gene}. "
        else:
            # Calculate percentage
            msg = f"{num_seq} / {num_attempted} ({(num_seq / num_attempted) * 100:.1f}%) samples successfully sequenced for {gene}. "

    return msg


def create_mutations_dict() -> dict:
    # Load drug resistance details from YAML file
    filepath = script_dir.parent / "drug_resistance_mutations.yml"
    with open(filepath, "r") as f:
        mut_dict = yaml.safe_load(f)

    return mut_dict

from warehouse.metadata.metadata import ExpThroughputDataScheme

# Tryptich across top of page
TRYPTICH = "tryptich"
TRYPTICH_EXP = TRYPTICH + ExpThroughputDataScheme.EXPERIMENTS
TRYPTICH_RXN = TRYPTICH + ExpThroughputDataScheme.REACTIONS
TRYPTICH_SAMPLE = TRYPTICH + ExpThroughputDataScheme.SAMPLES
TRYPTICH_LIST = [TRYPTICH_EXP, TRYPTICH_RXN, TRYPTICH_SAMPLE]


##################
# seq_qc outputs
SEQ_QC_EXPT_CHART_TYPE="seq_qc_select_chart_type"
SEQ_QC_EXPT_LIST="seq_experiment_list"
SEQ_SELECT_ALL_EXPTS_BUTTON="select_all_expts_button"
SEQ_QC_EXPT_CHART="seq_qc_chart"

# Not currently used:
SEQ_QC_SCALE_BUTTON = "seq_qc_scale_button"
SEQ_QC_PCT_NUM_BUTTON = "seq_qc_percent_number_button"
SEQ_QC_EXPT_SELECTOR="seq_qc_expt_selector"
SEQ_QC_SAMPLE_TYPE_SELECTOR="seq_qc_controls_samples_selector"


# Dropdowns for data selection
DATASOURCES = "datasource_dropdown"
DYNAMIC_OPTIONS = "dynamic_dropdown"
SELECTABLE_SCATTER = "selectable_scatter"

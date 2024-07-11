from metadata.metadata import ExpThroughputDataScheme

#Tryptich across top of page
TRYPTICH = "tryptich"
TRYPTICH_EXP = TRYPTICH + ExpThroughputDataScheme.EXPERIMENTS
TRYPTICH_RXN = TRYPTICH + ExpThroughputDataScheme.REACTIONS
TRYPTICH_SAMPLE= TRYPTICH + ExpThroughputDataScheme.SAMPLES
TRYPTICH_LIST= [ TRYPTICH_EXP, TRYPTICH_RXN, TRYPTICH_SAMPLE]

#Summary plots of seq output
SEQ_OUTPUT = "sequencing_output_reads"
SEQ_OUTPUT_SCALE_BUTTON = "seq_output_scale_button"

#Dropdowns for data selection
DATASOURCE_DROPDOWN="datasource_dropdown"
COLUMN_DROPDOWN="dynamic_dropdown"
SELECTABLE_SCATTER="selectable_scatter"
from lib.dataschemas import ExpThroughputDataScheme

#Tryptich across top of page
TRYPTICH = "tryptich"
TRYPTICH_EXP = TRYPTICH + ExpThroughputDataScheme.EXPERIMENTS
TRYPTICH_RXN = TRYPTICH + ExpThroughputDataScheme.REACTIONS
TRYPTICH_SAMPLE= TRYPTICH + ExpThroughputDataScheme.SAMPLES
TRYPTICH_LIST= [ TRYPTICH_EXP, TRYPTICH_RXN, TRYPTICH_SAMPLE]

#Summary plots of seq output
SEQ_OUTPUT = "sequencing_output_reads"
SEQ_OUTPUT_SCALE_BUTTON = "seq_output_scale_button"


#NOT UISED
# DATASOURCE_DROPDOWN="Datasource"
# COLUMN_DROPDOWN="ColumnDropDown"

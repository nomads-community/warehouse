class SampleDataSchema:
    # References for sample data
    SAMPLEID = "Sample ID"
    DATE = "Date Collected"
    PARASITAEMIA = "Parasitaemia (p/ul)"
    LOCATION = "Province"
    MONTH = "Month"
    YEAR = "Year"
    STATUS = "Status"

class ExpDataSchema:
    # References for experimental data
    
    # Experiment Level
    EXP_ID = "expt_id"
    EXP_DATE = "expt_date"
    EXP_TYPE= "expt_type"
    EXP_USER = "expt_user"
    EXP_VERSION = "expt_version"
    EXP_RXNS = "expt_rxns"
    EXP_NOTES = "expt_notes"
    EXP_SUMMARY = "expt_summary"
    # sWGA Specific
    SWGA_RXN_VOL_ul = "swga_rxnvol_ul"	
    SWGA_TARGETMASS = "swga_targetmass_ng"
    # PCR Specific
    PCR_PRIMERS = "pcr_primers"
    PCR_PRIMER_SOURCE = "pcr_primersource"
    PCR_TARGETPANEL = "pcr_targetpanel"
    PCR_ENZYME = "pcr_enzyme"
    #Sequence Library specific
    ENDREPARIS_TARGETMASS_ng = "endrepair_targetmass_ng"
    ENDREPAIR_MAXVOL_ul = "endrepair_maxvol_ul"	
    ENDREPAIR_DNA_ngul = "endrepair_dnaconc_ngul"
    ADAPTLIG_TARGETMASS_ng = "adaptlig_targetmass_ng"
    ADAPTLIG_MAXVOL_ul = "adaptlig_maxvol_ul"
    SEQLIB_DNACONC_ngul = "library_dnaconc_ngul"
    SEQ_PLATFORM = "seq_platform"
    FLOWCELL_TARGETMASS_ng = "flowcell_targetmass_ng"
    FLOWCELL_MAXVOL_ul = "flowcell_maxvol_ul"
    FLOWCELL_ID = "flowcell_id"
    FLOWCELL_CHEMISTRY = "flowcell_chemistry"
    FLOWCELL_STATUS = "flowcell_status"
    FLOWCELL_CHECKPORES = "flowcell_checkpores"
    FLOWCELL_RUNLENGTH_hrs = "flowcell_runlength_hrs"
    FLOWCELL_PREVUSE_hrs = "flowcell_prevusage_hrs"
 
    # Individual reactions
    SAMPLEID = "sample_id"
    EXTRACTIONID = "extraction_id"
    # sWGA Specific
    SWGA_IDENTIFIER = "swga_identifier"
    SWGA_TEMPLATE_VOL = "swga_template_ul"
    SWGA_PRODUCT_ngul = "swga_product_ngul"
    #PCR Specific
    PCR_IDENTIFIER = "pcr_identifier"
    PCR_PRODUCT_ngul = "pcr_product_ngul"
    #Sequence Library specific
    SEQLIB_IDENTIFIER = "seqlib_identifier"
    BARCODE = "barcode"
    ENDREPARI_VOL_ul = "endrepair_vol_ul"

class SeqDataSchema:
    # References for sequencing data

    # FROM NOMADIC3 SUMMARY BAM   
    # Sample Info
    EXP_ID = "expt_id"
    BARCODE = "barcode"
    EXTRACTION_ID='extraction_id'
    SAMPLE_ID='sample_id'

    #Outputs
    N_TOTAL_READS='n_total'
    N_MAPPED='n_mapped'
    N_UNMAPPED='n_unmapped'
    N_PRIMARY='n_primary'
    N_SECONDARY='n_secondary'
    N_CHIMERA='n_chimeria'

    #Lists for quick reference and in order of first to plot
    MAPPED_LIST=[N_PRIMARY, N_SECONDARY, N_CHIMERA, N_UNMAPPED]

class ExpThroughputDataScheme:
    SAMPLES= "experiments"
    EXPERIMENTS= "reactions"
    REACTIONS= "samples"
    # Define list so it is ordered
    EXP_TYPES = ['Not tested', 'sWGA','PCR','seqlib'] 

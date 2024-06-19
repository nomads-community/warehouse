class SampleDataSchema:
    #### REFERENCES FOR ALL SAMPLE METADATA #####
    SAMPLE_ID = "Sample ID"
    DATE = "Date Collected"
    PARASITAEMIA = "Parasitaemia (p/ul)"
    LOCATION = "Province"
    MONTH = "Month"
    YEAR = "Year"
    STATUS = "Status"
    ALL_VARS_DICT = { DATE : "Date",
                   PARASITAEMIA : "Parasitaemia",
                   LOCATION : "Location",
                   MONTH : "Month collected",
                   YEAR : "Year collected" 
                   }

class ExpDataSchema:
    #### REFERENCES FOR ALL EXPERIMENTAL DATA INCLUDING EXPT LEVEL AND INDIVIDUAL RXN #####
    
    # Experiment Level fields are common to all experiments and are suffixed with the
    # experiment type e.g. expt_id_swga in the all_df
    EXP_ID = "expt_id"
    EXP_DATE = "expt_date"
    EXP_TYPE= "expt_type"
    EXP_USER = "expt_user"
    EXP_VERSION = "expt_version"
    EXP_RXNS = "expt_rxns"
    EXP_NOTES = "expt_notes"
    EXP_SUMMARY = "expt_summary"

    # These fields are common to all experiment types. Once joined with other types they will 
    # have suffixes e.g. -swga.
    EXP_COMMON_FIELDS = {
        EXP_ID : "Experiment ID",
        EXP_DATE: "Experiment Date",
        EXP_USER: "User",
        EXP_VERSION: "Template version",
    }
    # Create a new dictionary with modified keys and values
    EXP_COMMON_FIELDS_SWGA = {key + "_sWGA": value + " (sWGA)" for key, value in EXP_COMMON_FIELDS.items()}
    EXP_COMMON_FIELDS_PCR = {key + "_PCR": value + " (PCR)" for key, value in EXP_COMMON_FIELDS.items()}
    EXP_COMMON_FIELDS_SEQLIB = {key + "_seqlib": value + " (seqlib)" for key, value in EXP_COMMON_FIELDS.items()}

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
    SAMPLE_ID = "sample_id"
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
    
    #Searchables are dict containing the key value pairs
    SWGA_VARS_DICT = { SWGA_RXN_VOL_ul : "Reaction Volume (ul)",
                        SWGA_TARGETMASS : "Target mass (ng)", 
                        SWGA_TEMPLATE_VOL: "Template volume (ul)",
                        SWGA_PRODUCT_ngul : "DNA conc of product (ng/ul)" 
                        } | EXP_COMMON_FIELDS_SWGA
    PCR_VARS_DICT = { PCR_PRIMERS : "Primer Set",
                       PCR_PRIMER_SOURCE : "Primer source",
                       PCR_TARGETPANEL : "NOMADS Target", 
                       PCR_ENZYME : "Enzyme used", 
                       PCR_PRODUCT_ngul : "DNA conc of product (ng/ul)"
                       } | EXP_COMMON_FIELDS_PCR

    SEQ_VARS_DICT = { ENDREPARIS_TARGETMASS_ng : "DNA mass for end-repair (ng)",
                 ENDREPAIR_MAXVOL_ul : "Max rxn vol for end-repair (ul)", 
                 ENDREPAIR_DNA_ngul : "End Repair DNA conc (ng/ul)",
                 ADAPTLIG_TARGETMASS_ng : "Target mass for adaptor ligation (ng)",
                 ADAPTLIG_MAXVOL_ul : "Max volume for adaptor ligation (ul)",
                 SEQLIB_DNACONC_ngul : "DNA conc of library (ng/ul)",
                 SEQ_PLATFORM : "Sequencing platform",
                 FLOWCELL_TARGETMASS_ng : "Target DNA mass to load (ng)", 
                 FLOWCELL_MAXVOL_ul : "Max volume of library to load (ul)",
                 FLOWCELL_ID : "Flowcell ID",
                 FLOWCELL_CHEMISTRY : "Flowcell chemistry",
                 FLOWCELL_STATUS : "Flowcell status",
                 FLOWCELL_CHECKPORES : "Flowcell pores available pre-run",
                 FLOWCELL_RUNLENGTH_hrs : "Run time length (hrs)",
                 FLOWCELL_PREVUSE_hrs : "Previous hrs flowcell run for" 
                 } | EXP_COMMON_FIELDS_SEQLIB
    
    #This is the master dict for all translations from key to value for Experimental fields
    ALL_VARS_DICT = SWGA_VARS_DICT | PCR_VARS_DICT | SEQ_VARS_DICT

class SeqDataSchema:
    #### REFERENCES FOR ALL SEQUENCE DATA GENERATED BY NOMADIC OR SAVANNAH #####

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
    MAPPED_LIST=[ N_PRIMARY, N_SECONDARY, N_CHIMERA, N_UNMAPPED ]

    #This is the master dict for all translations from key to value for Sequence Data fields
    ALL_VARS_DICT = { N_TOTAL_READS : "Total reads (n)",
                 N_MAPPED : "Total mapped reads (n)",
                 N_UNMAPPED : "Total unmapped reads (n)",
                 N_PRIMARY : "Primary mapped reads (n)",
                 N_SECONDARY : "Secondary mapped reads (n)",
                 N_CHIMERA : "Chimera mapped reads (n)"
                 }
   
class ExpThroughputDataScheme:
    #### Definitions for making the summary throughput calculations #####
    SAMPLES= "experiments"
    EXPERIMENTS= "reactions"
    REACTIONS= "samples"
    # Define list so it is ordered
    EXP_TYPES = ['Not tested', 'sWGA','PCR','seqlib']

class DataSources:
    #### REFERENCES FOR DATA SOURCES FOR USER SELECTION #####
    
    #All data sources
    DATA_SOURCE_DICT = {"sWGA": "Experimental (sWGA)",
                   "PCR": "Experimental (PCR)",
                   "seqlib": "Experimental (seqlib)",
                   "sample": "Sample information",
                   "seqdata": "Sequence Analysis (nomadic)"
                   }
    
    #List of variable names for each data source
    VAR_DICT_BY_SOURCE = {"sWGA": ExpDataSchema.SWGA_VARS_DICT,
                    "PCR": ExpDataSchema.PCR_VARS_DICT,
                    "seqlib": ExpDataSchema.SEQ_VARS_DICT,
                    "sample": SampleDataSchema.ALL_VARS_DICT,
                    "seqdata": SeqDataSchema.ALL_VARS_DICT,
    }

    #This is the master dict for all translations from key to value for all fields
    ALL_VARS_DICT = SampleDataSchema.ALL_VARS_DICT | ExpDataSchema.ALL_VARS_DICT | SeqDataSchema.ALL_VARS_DICT

    # @classmethod
    # def get_all_variables(cls):
    #     # Get all public attributes (excluding methods) starting with uppercase
    #     return [attr for attr in cls.__dict__.keys() if not attr.startswith("_") and attr.isupper()]

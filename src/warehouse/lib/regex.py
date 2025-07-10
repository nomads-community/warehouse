import re


class Regex_patterns:
    # Identifying NOMADS specific files
    NOMADS_EXPID = re.compile(r"(SW|PC|SL)[a-zA-Z]{2}[0-9]{3}")
    NOMADS_EXP_TEMPLATE = re.compile(r".*(SW|PC|SL)[a-zA-Z]{2}[0-9]{3}.*.xls(x|m)")

    # OTHER TYPES
    EXCEL_FILE = re.compile(r".*.xls(x|m)")
    EXCEL_CSV_FILE = re.compile(r".*.(xlsx|csv)")

    # Files that are open
    EXCEL_OPEN_FILES = re.compile(r"^[/.|~]")
    CSV_OPEN_FILES = re.compile(r"~lock")
    OPENFILES = re.compile("|".join([EXCEL_OPEN_FILES.pattern, CSV_OPEN_FILES.pattern]))

    # Sequence Data filetypes
    SEQDATA_BAMSTATS_CSV = re.compile(r".*summary.bamstats.*.csv")
    SEQDATA_BEDCOV_CSV = re.compile(r".*summary.bedcov.*.csv")
    SEQDATA_QC_PER_SAMPLE_CSV = re.compile(r".*summary.sample_qc.*.csv")
    SEQDATA_QC_PER_EXPT_JSON = re.compile(r".*summary.experiment_qc.*.json")
    SEQDATA_BCFTOOLS_OUTPUT_TSV = re.compile(r"bcftools.filtered.annotated.*.tsv")

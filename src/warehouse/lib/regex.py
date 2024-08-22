import re


class Regex_patterns:
    # Identifying NOMADS specific files
    NOMADS_EXPID = re.compile(r"(SW|PC|SL)[a-zA-Z]{2}[0-9]{3}")
    NOMADS_EXP_TEMPLATE = re.compile(r".*(SW|PC|SL)[a-zA-Z]{2}[0-9]{3}.*.xls(x|m)")

    # Files that are open
    EXCEL_FILES = re.compile(r"^[/.|~]")
    CSV_FILES = re.compile(r"~lock")
    OPENFILES = re.compile("|".join([EXCEL_FILES.pattern, CSV_FILES.pattern]))

    # Sequence Data filetypes
    SEQDATA_BAMSTATS_CSV = re.compile(r".*summary.bamstats.*.csv")
    SEQDATA_BEDCOV_CSV = re.compile(r".*summary.bedcov.*.csv")
    SEQDATA_EXPTQC_CSV = re.compile(r".*summary.sample_qc.*.csv")

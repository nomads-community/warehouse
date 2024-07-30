class DataFormatError(Exception):
    """Error in format or contents of the data"""

    pass


class DateFormatError(Exception):
    """Date format is incorrect."""

    pass


class PathError(Exception):
    """Failure to identify path"""

    pass

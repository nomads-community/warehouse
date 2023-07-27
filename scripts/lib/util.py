from datetime import datetime
from .exceptions import DateFormatError

def is_valid_format(date: str, format: str="%Y-%m-%d") -> None:
    """ Check that a `date` adheres to a given `format` """
    try:
        datetime.strptime(date, format)
    except ValueError:
        raise DateFormatError(f"Date {date} does not adhere to expected format: {format}.")
    

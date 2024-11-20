# imports

from datetime import datetime

# static var

datetime_format = "%m/%d/%Y %H:%M:%S"                                # format for the datetime variable

# functions

def get_datetime_now() -> str :
    """
    get_datetime_now -- This function will generate a strig representing the
    time given the format specified.

    Returns:
        the string representing the moment in time down to seconds
    """
    return datetime.now().strftime(datetime_format)
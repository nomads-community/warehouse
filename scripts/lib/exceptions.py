

class MetadataFormatError(Exception):
    """Error in format or contents of the metadata"""

    pass

class InventoryError(Exception):
    """Inventory is missing or malformatted"""
    pass

class DateFormatError(Exception):
    """Date format is incorrect."""

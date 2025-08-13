def get_initials(name):
    """
    Converts a full name to initials.
    """
    # Split the name into words
    words = name.split()
    # Get the first letter of each word and join them
    initials = "".join([word[0] for word in words]).upper()
    return initials

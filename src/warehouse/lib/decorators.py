from functools import wraps

def singleton(cls):
    # This dictionary holds instances of each class decorated with @singleton
    instances = {}

    # This inner function is responsible for managing instances
    @wraps(cls)
    def get_instance(*args, **kwargs):
        # Check if an instance of 'cls' already exists
        if cls not in instances:
            # If not, create and store one
            instances[cls] = cls(*args, **kwargs)
        # Return the instance of 'cls'
        return instances[cls]

    # Return the inner function
    return get_instance
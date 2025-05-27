import os
from functools import wraps


def set_pytest_env():
    os.environ['ENV'] = 'pytest'


def mock_generic_custom_class(cls):
    """
    A decorator to mock MySQL for all methods in a class.
    This version wraps each method in the class with the mock_sql_decorator.
    """
    for attr_name, attr_value in cls.__dict__.items():
        # Check if the attribute is a callable (method) and not a dunder method
        if callable(attr_value) and not attr_name.startswith("__"):
            # Wrap the method with the SQL mocking logic`
            wrapped_method = mock_generic_decorator(attr_value)
            # Replace the original method with the wrapped one
            setattr(cls, attr_name, wrapped_method)

    return cls


def mock_generic_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        set_pytest_env()
        return func(*args, **kwargs)

    return wrapper

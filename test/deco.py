#!/usr/bin/env python3


from typing import Callable


def my_decorator(func: Callable):
    def wrapper(*args, **kwargs):
        print("Arguments passed to the function:", args, kwargs)
        print(func.__name__)
        print(func.__annotations__)
        return func(*args, **kwargs)  # Call the original function

    return wrapper


@my_decorator
def greet(name: str, age: int = 30):
    print(f"Hello, {name}! You are {age} years old.")


greet("Alice", age=25)

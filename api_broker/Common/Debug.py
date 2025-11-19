import inspect

def func_name(depth=1):
    if len(inspect.stack()) > depth:
        return inspect.stack()[1].function

    return "None"
import inspect

def func_name(depth=1):
    if len(inspect.stack()) > depth:
        return inspect.stack()[depth].function

    return "None"

def Error(*values):
    print(f"[ Error : {func_name(depth=2)} ]")
    print(*values)

def Info(*values):
    print(f"[ Info : {func_name(depth=2)} ]")
    print(*values)
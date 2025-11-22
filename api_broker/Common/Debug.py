import inspect
import os

def func_name(depth=2):
    if len(inspect.stack()) > depth:
        return inspect.stack()[depth].function

    return "None"

def file_name(depth=2):
    try:
        if len(inspect.stack()) > depth:
            return inspect.stack()[depth].filename
            #return os.path.basename(inspect.stack()[depth].filename)
    except:
        pass
    
    return "None"

def Error(*values):
    print(f"[ Error : {file_name()} / {func_name()} ]")
    print(*values)

def Info(*values):
    print(f"[ Info : {file_name()} / {func_name()} ]")
    print(*values)
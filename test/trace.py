import sys

depth = 0


def trace_calls(frame, event, arg):
    global depth

    if event == "call":
        print("  " * depth + f"CALL   {frame.f_code.co_name} ({frame.f_code.co_filename}:{frame.f_lineno})")
        depth += 1
        return trace_calls

    if event == "return":
        depth -= 1
        print("  " * depth + f"RETURN {frame.f_code.co_name} -> {arg!r}")

    return trace_calls


def foo():
    bar()
    baz()


def bar():
    print("hello")


def baz():
    pass


sys.settrace(trace_calls)
foo()
sys.settrace(None)

#!/usr/bin/env python3


import ast
import json

from typing import Any


def unparseCall(x: ast.Call) -> list:
    if type(x.func) == ast.Attribute:
        if type(x.func.value) == ast.Name:
            return ["Call", x.func.attr, [["Call", "load", [x.func.value.id]]] + list(map(unparse, x.args))]
        return ["Call", x.func.attr, [unparse(x.func.value)] + list(map(unparse, x.args))]
    return ["Call", unparse(x.func), list(map(unparse, x.args))]


def unparseAssign(x: ast.Assign) -> list:
    return ["Assign", unparse(x.targets[0]), unparse(x.value)]


def unparseSubscript(x: ast.Subscript) -> list:
    return ["Subscript", unparse(x.value), unparse(x.slice)]


def unparseSlice(x: ast.Slice) -> list:
    return [unparse(x.lower) if x.lower else 0, unparse(x.upper) if x.upper else -1]


def unparse(x: Any) -> Any:
    mapUnparse = {
        ast.Expr: lambda x: unparse(x.value),
        ast.Call: unparseCall,
        ast.Assign: unparseAssign,
        ast.Subscript: unparseSubscript,
        ast.Slice: unparseSlice,
        ast.Constant: lambda x: x.value,
        ast.Name: lambda x: x.id,
        list: lambda x: list(map(unparse, x)),
    }

    try:
        return mapUnparse[type(x)](x)
    except:
        print(x, [(i, getattr(x, i)) for i in x._fields])
        return x


def unparseAst(x: ast.Module):
    expr = []
    for e in getattr(x, "body"):
        if type(e).__name__ == "ImportFrom":
            continue
        expr.append(e)

    return [unparse(e) for e in expr]


def commentsToLabel(s: str) -> str:
    if s == "":
        return ""
    if s[0] != "#":
        return s[0] + commentsToLabel(s[1:])
    i = 2
    while s[i] != "\n":
        i += 1
    return f'label("{s[2:i]}")' + commentsToLabel(s[i:])


def toJson(filepath: str) -> str:

    # Read the content of the file
    with open(filepath, "r") as file:
        content = commentsToLabel(file.read())

    # Parse the file content into an AST
    parsedAst = ast.parse(content)
    # print(f"parsedAst=[{ast.dump(parsedAst, indent=4)}]")

    # Parse the ast and convert it to a list of instructions
    unparsedAst = unparseAst(parsedAst)
    # print(f"unparsedAst=[{unparsedAst}]")

    # Serialize the instructions to JSON
    return json.dumps(unparsedAst)


if __name__ == "__main__":
    print(toJson("video.py"))

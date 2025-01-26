#!/usr/bin/env python3


import ast
import json

from typing import Any


def unparseCall(x: ast.Call) -> list:
    return [type(x).__name__, unparse(x.func), list(map(unparse, x.args))]


def unparseAssign(x: ast.Assign) -> list:
    return [type(x).__name__, unparse(x.targets[0]), unparse(x.value)]


def unparse(x: Any) -> Any:
    mapUnparse = {
        ast.Expr: lambda x: unparse(x.value),
        ast.Call: unparseCall,
        ast.Assign: unparseAssign,
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
    parsedAst = unparseAst(ast.parse(content))

    # Convert the AST body into a dictionary and print it
    return json.dumps(parsedAst)

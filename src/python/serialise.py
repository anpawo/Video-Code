#!/usr/bin/env python3


import ast
import json

from typing import Any


def toLoad(id: str) -> list:
    return [["Call", "load", [id]]]


def unparseCall(x: ast.Call) -> list:
    if type(x.func) == ast.Attribute:
        if type(x.func.value) == ast.Name:
            l = ["Call", x.func.attr, toLoad(x.func.value.id) + list(map(unparse, x.args))]

            # Special case `concat`
            if l[:-1] == ["Call", "concat"]:
                return l[:-1] + [(l[-1][:-1] + toLoad(l[-1][-1]))]

            return l

        return ["Call", x.func.attr, [unparse(x.func.value)] + list(map(unparse, x.args))]

    l = ["Call", unparse(x.func), list(map(unparse, x.args))]

    # Special case `Label`
    if l[:-1] == ["Call", "label"]:
        return ["Label", l[-1][0]]

    return l


def unparseAssign(x: ast.Assign) -> list:
    if type(x.value) == ast.Name:
        return ["Assign", unparse(x.targets[0])] + toLoad(x.value.id)
    return ["Assign", unparse(x.targets[0]), unparse(x.value)]


def unparseSubscript(x: ast.Subscript) -> list:
    if type(x.value) == ast.Name:
        return ["Call", "subscript", toLoad(x.value.id) + unparse(x.slice)]
    return ["Call", "subscript", unparse(x.value) + unparse(x.slice)]


def unparseSlice(x: ast.Slice) -> list:
    return [unparse(x.lower) if x.lower else 0, unparse(x.upper) if x.upper else -1]


def unparseUnaryOp(x: ast.UnaryOp) -> int:  # type: ignore // only support negative -<x>
    if type(x.op) == ast.USub:
        return -x.operand.value  # type: ignore throw // otherwise


def unparse(x: Any) -> Any:
    mapUnparse = {
        ast.Expr: lambda x: unparse(x.value),
        ast.Call: unparseCall,
        ast.Assign: unparseAssign,
        ast.Subscript: unparseSubscript,
        ast.Slice: unparseSlice,
        ast.Constant: lambda x: x.value,
        ast.Name: lambda x: x.id,
        ast.UnaryOp: unparseUnaryOp,
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
    if s[0:3] != "\n# ":
        return s[0] + commentsToLabel(s[1:])
    i = 3
    while s[i] != "\n":
        i += 1
    return f'label("{s[3:i]}")' + commentsToLabel(s[i:])


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
    for i in json.loads(toJson("video.py")):
        print(i)

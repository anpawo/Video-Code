#!/usr/bin/env python3

import argparse
import inspect
import json
import os
import sys
import importlib.util
from types import ModuleType


ROOT = os.path.abspath(os.path.dirname(__file__) + "/..")
PKG_DIR = os.path.join(ROOT, "videocode")
sys.path.append(ROOT)
sys.path.insert(0, PKG_DIR)

# Force-load the package version of `videocode` to avoid the root-level `videocode.py` file.
pkg_init = os.path.join(PKG_DIR, "__init__.py")
pkg_spec = importlib.util.spec_from_file_location(
    "videocode",
    pkg_init,
    submodule_search_locations=[PKG_DIR],
)
if pkg_spec and pkg_spec.loader:
    pkg_module = importlib.util.module_from_spec(pkg_spec)
    sys.modules["videocode"] = pkg_module
    pkg_spec.loader.exec_module(pkg_module)

from videocode.input.input import Input
from videocode.shader.ishader import IShader, VertexShader, FragmentShader

try:
    from videocode.utils.bezier import Easing as VCEasing, cubicBezier as VCCubicBezier
except Exception:
    VCEasing = None
    VCCubicBezier = None

try:
    from utils.bezier import Easing as UEasing, cubicBezier as UCubicBezier
except Exception:
    UEasing = None
    UCubicBezier = None

# Load inputs and shaders by importing their aggregators
import videocode.input._inputs  # noqa: F401
import videocode.shader._shaders  # noqa: F401


def iter_subclasses(base):
    seen = set()
    work = list(base.__subclasses__())
    while work:
        cls = work.pop()
        if cls in seen:
            continue
        seen.add(cls)
        work.extend(cls.__subclasses__())
    return seen


def format_annotation(ann):
    if ann is inspect._empty:
        return "Any"
    if isinstance(ann, type):
        return ann.__name__
    s = repr(ann)
    return s.replace("typing.", "")


def format_default(value):
    if value is None:
        return "None"
    if isinstance(value, (int, float, bool, str)):
        return repr(value)

    # Try to map easing objects to readable names
    easing_maps = []
    if VCEasing:
        easing_maps.append((VCEasing, VCCubicBezier))
    if UEasing:
        easing_maps.append((UEasing, UCubicBezier))

    for easing_cls, cubic_cls in easing_maps:
        if cubic_cls and isinstance(value, cubic_cls):
            for name in ("Linear", "In", "Out", "InOut"):
                if getattr(easing_cls, name, None) is value:
                    return f"Easing.{name}"
            return "cubicBezier"

    return value.__class__.__name__


def format_signature(name, sig):
    params = []
    for p in sig.parameters.values():
        if p.name == "self":
            continue
        ann = format_annotation(p.annotation)
        if p.default is inspect._empty:
            params.append(f"{p.name}: {ann}")
        else:
            params.append(f"{p.name}: {ann} = {format_default(p.default)}")
    return f"{name}({', '.join(params)})"


def code_signature(func):
    code = func.__code__
    argcount = code.co_argcount
    kwonlycount = code.co_kwonlyargcount
    varnames = list(code.co_varnames)

    args = varnames[:argcount]
    kwonly = varnames[argcount:argcount + kwonlycount]

    defaults = func.__defaults__ or ()
    kwdefaults = func.__kwdefaults__ or {}

    params = []
    if args:
        defaults_offset = len(args) - len(defaults)
        for i, name in enumerate(args):
            if name == "self":
                continue
            if i >= defaults_offset:
                default_value = defaults[i - defaults_offset]
                params.append(f"{name}: Any = {format_default(default_value)}")
            else:
                params.append(f"{name}: Any")

    for name in kwonly:
        if name == "self":
            continue
        if name in kwdefaults:
            params.append(f"{name}: Any = {format_default(kwdefaults[name])}")
        else:
            params.append(f"{name}: Any")

    return f"{func.__name__}({', '.join(params)})"


def params_from_signature(sig):
    params = []
    for p in sig.parameters.values():
        if p.name == "self":
            continue
        ann = format_annotation(p.annotation)
        if p.default is inspect._empty:
            params.append({"name": p.name, "type": ann, "default": None})
        else:
            params.append({"name": p.name, "type": ann, "default": format_default(p.default)})
    return params


def params_from_code(func):
    code = func.__code__
    argcount = code.co_argcount
    kwonlycount = code.co_kwonlyargcount
    varnames = list(code.co_varnames)

    args = varnames[:argcount]
    kwonly = varnames[argcount:argcount + kwonlycount]

    defaults = func.__defaults__ or ()
    kwdefaults = func.__kwdefaults__ or {}

    params = []
    if args:
        defaults_offset = len(args) - len(defaults)
        for i, name in enumerate(args):
            if name == "self":
                continue
            if i >= defaults_offset:
                default_value = defaults[i - defaults_offset]
                params.append({"name": name, "type": "Any", "default": format_default(default_value)})
            else:
                params.append({"name": name, "type": "Any", "default": None})

    for name in kwonly:
        if name == "self":
            continue
        if name in kwdefaults:
            params.append({"name": name, "type": "Any", "default": format_default(kwdefaults[name])})
        else:
            params.append({"name": name, "type": "Any", "default": None})

    return params


def format_callable(callable_obj, name_override=None):
    name = name_override or callable_obj.__name__
    try:
        sig = inspect.signature(callable_obj, eval_str=False)
        return format_signature(name, sig)
    except Exception:
        sig = code_signature(callable_obj)
        return sig.replace(callable_obj.__name__, name, 1)


def param_list(callable_obj):
    try:
        sig = inspect.signature(callable_obj, eval_str=False)
        return params_from_signature(sig)
    except Exception:
        return params_from_code(callable_obj)


def load_module_from_path(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


def collect_inputs():
    inputs = []
    for cls in sorted(iter_subclasses(Input), key=lambda c: c.__name__):
        if cls in (Input,):
            continue
        if not cls.__module__.startswith("videocode.input"):
            continue
        annotations = getattr(cls, "__annotations__", {}) or {}
        if annotations:
            params = [{"name": k, "type": format_annotation(v), "default": None} for k, v in annotations.items()]
            inputs.append({"name": cls.__name__, "params": params})
        else:
            inputs.append({"name": cls.__name__, "params": param_list(cls.__init__)})
    return inputs


def collect_shaders():
    vertex = []
    fragment = []
    for cls in sorted(iter_subclasses(IShader), key=lambda c: c.__name__):
        if cls in (IShader, VertexShader, FragmentShader):
            continue
        if not cls.__module__.startswith("videocode.shader"):
            continue
        if issubclass(cls, VertexShader):
            vertex.append({"name": cls.__name__, "params": param_list(cls.__init__)})
        elif issubclass(cls, FragmentShader):
            fragment.append({"name": cls.__name__, "params": param_list(cls.__init__)})
    return vertex, fragment


def collect_templates():
    templates = []
    effect_dir = os.path.join(ROOT, "videocode", "template", "effect")
    for filename in sorted(os.listdir(effect_dir)):
        if not filename.endswith(".py") or filename.startswith("__"):
            continue
        path = os.path.join(effect_dir, filename)
        module_name = f"videocode.template.effect.{filename[:-3]}"
        module = load_module_from_path(path, module_name)
        if module is None:
            continue
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ != module.__name__:
                continue
            if name.startswith("_"):
                continue
            templates.append({"name": name, "params": param_list(obj)})
    return templates


def collect_input_methods():
    methods = []
    for name, obj in inspect.getmembers(Input, inspect.isfunction):
        if name.startswith("_"):
            continue
        if obj.__qualname__.split(".")[0] != "Input":
            continue
        if name in ("apply", "flush"):
            continue
        methods.append({"name": name, "params": param_list(obj)})
    return methods


def print_section(title, entries):
    print(f"\n[{title}]")
    if not entries:
        print("- (none)")
        return
    for e in entries:
        params = ", ".join(
            [
                f"{p['name']}: {p['type']}" + (f" = {p['default']}" if p['default'] is not None else "")
                for p in e.get("params", [])
            ]
        )
        print(f"- {e['name']}({params})")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--json", action="store_true")
    args, _ = parser.parse_known_args()

    inputs = collect_inputs()
    vertex, fragment = collect_shaders()
    templates = collect_templates()
    methods = collect_input_methods()

    if args.json:
        payload = {
            "inputs": inputs,
            "shaders": {"vertex": vertex, "fragment": fragment},
            "templates": templates,
            "helpers": methods,
        }
        print(json.dumps(payload))
    else:
        print_section("Inputs", inputs)
        print_section("Shaders: Vertex", vertex)
        print_section("Shaders: Fragment", fragment)
        print_section("Templates", templates)
        print_section("Input Helpers", methods)


if __name__ == "__main__":
    main()

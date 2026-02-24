#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any


DEFAULT_PLUGIN_DIR = "plugins/build"


def _plugin_dirs() -> list[Path]:
    raw = os.getenv("VIDEO_CODE_PLUGIN_DIR", DEFAULT_PLUGIN_DIR)
    return [Path(p) for p in raw.split(os.pathsep) if p]


def _resolve_plugin_file(metadata_path: Path, relative_or_absolute: str) -> Path:
    path = Path(relative_or_absolute)
    if path.is_absolute():
        return path
    return metadata_path.parent / path


def load_python_plugins(target_globals: dict[str, Any]) -> None:
    for plugin_dir in _plugin_dirs():
        if not plugin_dir.exists():
            continue

        for metadata_path in plugin_dir.rglob("*.json"):
            with metadata_path.open("r", encoding="utf-8") as f:
                metadata = json.load(f)

            module_location = metadata.get("python_module")
            if module_location is None:
                continue

            module_path = _resolve_plugin_file(metadata_path, module_location)
            if module_path.suffix != ".py" or not module_path.exists():
                continue

            module_name = f"vc_plugin_{metadata.get('name', module_path.stem).replace('-', '_')}"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "register"):
                module.register(target_globals)
                continue

            exported = getattr(module, "__all__", [])
            for symbol in exported:
                target_globals[symbol] = getattr(module, symbol)

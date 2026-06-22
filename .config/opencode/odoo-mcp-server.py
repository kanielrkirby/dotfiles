#!/usr/bin/env python3
"""Launch the Odoo MCP server from a config file.

Search order:
- `OPENCODE_ODOO_CONFIG` if set
- `./.opencode/plugins/odoo/config.json` walking upward from cwd
- `~/.config/opencode/plugins/odoo/config.json`

Config format:
- Single profile: {"url": "...", "db": "...", ...}
- Multiple profiles: {"defaultConnection": "name", "connections": {"name": {...}}}
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


PROJECT_CONFIG_RELATIVE = Path(".opencode") / "plugins" / "odoo" / "config.json"
GLOBAL_CONFIG = Path.home() / ".config" / "opencode" / "plugins" / "odoo" / "config.json"
VENV_DIR = Path.home() / ".cache" / "opencode" / "odoo-mcp-venv"
REPO_URL = "git+https://github.com/hmcqueen/mcp-odoo"
LOG_FILE = Path.home() / ".config" / "opencode" / "odoo-mcp.log"


def log(message: str) -> None:
    line = message.rstrip("\n")
    print(line, file=sys.stderr)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception:
        pass


def collect_config_paths() -> list[Path]:
    override = os.environ.get("OPENCODE_ODOO_CONFIG")
    if override:
        candidate = Path(override).expanduser()
        log(f"Odoo config selection: OPENCODE_ODOO_CONFIG={candidate}")
        if candidate.exists():
            log(f"Odoo config selected: {candidate} (override)")
            return [candidate]
        log(f"Odoo config missing: {candidate}")
        return []

    project_configs: list[Path] = []
    current = Path.cwd()
    while True:
        candidate = current / PROJECT_CONFIG_RELATIVE
        log(f"Odoo config probe: {candidate}")
        if candidate.exists():
            log(f"Odoo config selected: {candidate} (project)")
            project_configs.append(candidate)
        if current.parent == current:
            break
        current = current.parent

    config_paths: list[Path] = []
    if GLOBAL_CONFIG.exists():
        log(f"Odoo config selected: {GLOBAL_CONFIG} (global)")
        config_paths.append(GLOBAL_CONFIG)

    config_paths.extend(reversed(project_configs))

    if not config_paths:
        log("Odoo config selection: no config found")

    return config_paths


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("configuration must be a JSON object")
    return data


def normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(config.get("connections"), dict):
        return config
    profile = {
        key: value
        for key, value in config.items()
        if key not in {"defaultConnection"}
    }
    return {"defaultConnection": "default", "connections": {"default": profile}}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = deep_merge(existing, value)
        else:
            merged[key] = value
    return merged


def load_merged_config(config_paths: list[Path]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for config_path in config_paths:
        merged = deep_merge(merged, normalize_config(load_json(config_path)))
    return merged


def pick_profile(config: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    connections = config.get("connections")
    if isinstance(connections, dict) and connections:
        selected = os.environ.get("ODOO_CONNECTION") or config.get("defaultConnection")
        if not selected:
            selected = next(iter(connections.keys()))
        profile = connections.get(selected)
        if not isinstance(profile, dict):
            raise ValueError(f"connection '{selected}' is missing or invalid")
        return selected, profile
    return "default", config


def merge_env(profile: Dict[str, Any]) -> Dict[str, str]:
    env: Dict[str, str] = {}

    def put(key: str, value: Any) -> None:
        if value is None:
            return
        env[key] = str(value)

    put("ODOO_URL", profile.get("url"))
    put("ODOO_DB", profile.get("db"))
    put("ODOO_USERNAME", profile.get("username"))

    api_key = profile.get("api_key") or profile.get("apiKey")
    password = profile.get("password")
    if api_key:
        put("ODOO_API_KEY", api_key)
        put("ODOO_PASSWORD", api_key)
    elif password:
        put("ODOO_PASSWORD", password)

    transport = profile.get("transport")
    if not transport:
        transport = "json2" if api_key else "xmlrpc"
    put("ODOO_TRANSPORT", transport)

    json2_header = profile.get("json2_database_header")
    if json2_header is None and transport == "json2":
        json2_header = 1
    if json2_header is not None:
        put("ODOO_JSON2_DATABASE_HEADER", json2_header)

    extra_env = profile.get("env")
    if isinstance(extra_env, dict):
        for key, value in extra_env.items():
            put(str(key), value)

    missing = [name for name in ("ODOO_URL", "ODOO_DB", "ODOO_USERNAME") if name not in env]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    if "ODOO_API_KEY" not in env and "ODOO_PASSWORD" not in env:
        raise ValueError("missing password/api_key")

    return env


def main() -> int:
    config_paths = collect_config_paths()
    if not config_paths:
        log(
            "No Odoo config found. Create ~/.config/opencode/plugins/odoo/config.json "
            "or .opencode/plugins/odoo/config.json in a project.",
        )
        return 1

    try:
        config = load_merged_config(config_paths)
        name, profile = pick_profile(config)
        env = os.environ.copy()
        env.update(merge_env(profile))
        if "ODOO_TRANSPORT" not in env:
            env["ODOO_TRANSPORT"] = "json2"
        if env.get("ODOO_TRANSPORT") == "json2" and "ODOO_JSON2_DATABASE_HEADER" not in env:
            env["ODOO_JSON2_DATABASE_HEADER"] = "1"
        resolved = ", ".join(str(path) for path in config_paths)
        log(f"Odoo config resolved: {resolved} (connection: {name})")
    except Exception as exc:
        log(f"Failed to load Odoo config from {config_paths}: {exc}")
        return 1

    try:
        python_bin = VENV_DIR / "bin" / "python"
        if not python_bin.exists():
            VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
            subprocess.run(
                [str(python_bin), "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                env=env,
            )
            subprocess.run(
                [str(python_bin), "-m", "pip", "install", REPO_URL],
                check=True,
                env=env,
            )

        raise SystemExit(subprocess.call([str(python_bin), "-m", "odoo_mcp"], env=env))
    except FileNotFoundError as exc:
        log(f"Python runtime missing: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

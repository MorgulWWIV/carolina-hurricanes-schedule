"""Configurable NHL team schedule board plugin metadata."""

import json
from pathlib import Path

_PLUGIN_FILE = Path(__file__).parent / "plugin.json"
with _PLUGIN_FILE.open("r", encoding="utf-8") as _file:
    _plugin = json.load(_file)

__plugin_id__ = _plugin.get("name", "carolina_schedule")
__version__ = _plugin.get("version", "1.0.0")
__description__ = _plugin.get("description", "Configurable NHL team schedule")
__board_name__ = "NHL Team Schedule"
__author__ = _plugin.get("author", "MorgulWWIV")
__requirements__ = _plugin.get("requirements", {})
__min_app_version__ = __requirements__.get("app_version", ">=2026.03.0")
__preserve_files__ = _plugin.get("preserve_files", [])

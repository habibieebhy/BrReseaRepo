"""Local CLI state with restrictive filesystem permissions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STATE_DIR = Path(".brixta")
STATE_FILE = STATE_DIR / "connection.json"


def save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    STATE_FILE.chmod(0o600)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))

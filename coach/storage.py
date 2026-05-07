import json
import os
from datetime import date
from pathlib import Path

DATA_DIR = Path.home() / ".english-coach"
SESSIONS_DIR = DATA_DIR / "sessions"
SCORECARD_PATH = DATA_DIR / "scorecard.json"
CONFIG_PATH = DATA_DIR / "config.json"


def ensure_dirs():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def save_session(data: dict, session_date: date = None) -> Path:
    ensure_dirs()
    d = session_date or date.today()
    path = SESSIONS_DIR / f"{d.isoformat()}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def load_session(session_date: date) -> dict | None:
    path = SESSIONS_DIR / f"{session_date.isoformat()}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def list_sessions() -> list[date]:
    ensure_dirs()
    sessions = []
    for p in sorted(SESSIONS_DIR.glob("*.json")):
        try:
            sessions.append(date.fromisoformat(p.stem))
        except ValueError:
            pass
    return sessions


def load_scorecard() -> dict:
    if not SCORECARD_PATH.exists():
        return {}
    with open(SCORECARD_PATH) as f:
        return json.load(f)


def save_scorecard(data: dict):
    ensure_dirs()
    with open(SCORECARD_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(data: dict):
    ensure_dirs()
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

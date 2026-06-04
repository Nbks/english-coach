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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def session_exists(session_date: date) -> bool:
    return (SESSIONS_DIR / f"{session_date.isoformat()}.json").exists()


def previous_session_date(session_date: date) -> date | None:
    sessions = [d for d in list_sessions() if d < session_date]
    return sessions[-1] if sessions else None


def load_session(session_date: date) -> dict | None:
    if not session_exists(session_date):
        return None
    with open(SESSIONS_DIR / f"{session_date.isoformat()}.json", encoding="utf-8") as f:
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
    with open(SCORECARD_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_scorecard(data: dict):
    ensure_dirs()
    with open(SCORECARD_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict):
    ensure_dirs()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

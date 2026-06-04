from datetime import date, timedelta
from . import storage

FULL_HISTORY_DAYS = 9      # días 1-9: contexto completo
ROLLING_WINDOW = 7         # día 10+: últimos 7 días completos

DEFAULT_SCORECARD = {
    "total_sessions": 0,
    "metrics": {
        "grammar": {"score": None, "trend": 0},
        "coherence": {"score": None, "trend": 0},
        "vocabulary": {"score": None, "trend": 0},
        "serious_errors": {"count": None, "trend": 0},
    },
    "prompt_version": 1,
    "notes": "",
}


# ── Scorecard ────────────────────────────────────────────────────────────────

def get_scorecard() -> dict:
    saved = storage.load_scorecard()
    # Merge con defaults para que nunca falten keys
    sc = {**DEFAULT_SCORECARD, **saved}
    sc["metrics"] = {**DEFAULT_SCORECARD["metrics"], **saved.get("metrics", {})}
    return sc


def update_scorecard(report: dict, session_date: date) -> dict:
    """
    Recibe el reporte del analyzer y actualiza el scorecard rolling.
    report debe tener:
        {
            "grammar_score": int (0-100),
            "coherence_score": int (0-100),
            "vocabulary_score": int (0-100),
            "serious_errors_count": int,
        }
    """
    sc = get_scorecard()

    if not storage.session_exists(session_date):
        sc["total_sessions"] += 1

    metrics = sc["metrics"]

    prev_date = storage.previous_session_date(session_date)
    prev_data = storage.load_session(prev_date) if prev_date else None

    def update_metric(key, new_value):
        metrics[key]["score"] = new_value
        if prev_data:
            old = prev_data.get(f"{key}_score")
            metrics[key]["trend"] = (new_value - old) if old is not None else 0
        else:
            metrics[key]["trend"] = 0

    update_metric("grammar", report.get("grammar_score", 0))
    update_metric("coherence", report.get("coherence_score", 0))
    update_metric("vocabulary", report.get("vocabulary_score", 0))

    sc["metrics"]["serious_errors"]["count"] = report.get("serious_errors_count", 0)
    if prev_data:
        prev_errors = prev_data.get("serious_errors_count")
        sc["metrics"]["serious_errors"]["trend"] = (
            report.get("serious_errors_count", 0) - prev_errors
        ) if prev_errors is not None else 0
    else:
        sc["metrics"]["serious_errors"]["trend"] = 0

    storage.save_scorecard(sc)
    return sc


# ── Contexto para el analyzer ─────────────────────────────────────────────────

def build_context() -> dict:
    """
    Devuelve el contexto que se le pasa al analyzer:
        {
            "scorecard": {...},
            "recent_sessions": [...],   # lista de dicts de sesiones recientes
            "mode": "full" | "rolling", # para saber cómo armamos el contexto
        }
    """
    all_sessions = storage.list_sessions()
    total = len(all_sessions)

    if total <= FULL_HISTORY_DAYS:
        # Primeros 9 días: pasamos todo
        sessions_to_load = all_sessions
        mode = "full"
    else:
        # Día 10+: solo los últimos ROLLING_WINDOW días
        sessions_to_load = all_sessions[-ROLLING_WINDOW:]
        mode = "rolling"

    recent = []
    for d in sessions_to_load:
        data = storage.load_session(d)
        if data:
            recent.append({"date": d.isoformat(), **data})

    return {
        "scorecard": get_scorecard(),
        "recent_sessions": recent,
        "mode": mode,
    }


def scorecard_summary(sc: dict) -> str:
    """Genera un resumen legible del scorecard para incluir en el prompt."""
    m = sc["metrics"]
    total = sc["total_sessions"]

    def fmt(metric, label):
        score = metric.get("score")
        trend = metric.get("trend", 0)
        if score is None:
            return f"  {label}: sin datos aún"
        arrow = "↑" if trend > 0 else ("↓" if trend < 0 else "→")
        return f"  {label}: {score}/100  {arrow}{abs(trend):+d} vs sesión anterior"

    serious = m["serious_errors"]
    serious_str = (
        f"  Errores graves: {serious['count']} esta sesión"
        if serious["count"] is not None
        else "  Errores graves: sin datos aún"
    )

    lines = [
        f"Total de sesiones: {total}",
        fmt(m["grammar"], "Gramática"),
        fmt(m["coherence"], "Coherencia"),
        fmt(m["vocabulary"], "Vocabulario"),
        serious_str,
    ]
    return "\n".join(lines)

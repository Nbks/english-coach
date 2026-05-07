import json

import anthropic

from .context import build_context, scorecard_summary

client = anthropic.Anthropic()
MODEL = "claude-opus-4-5"

BASE_PROMPT = """You are an English speaking coach. Your student records a daily 15-minute video speaking in English and you analyze the transcription.

Your job is to give honest, specific, and constructive feedback. Do not be generic.

## What to evaluate

1. **Grammar** (score 0-100)
   - Verb tenses, subject-verb agreement, articles (a/an/the), prepositions
   - Point out specific errors with corrections

2. **Coherence** (score 0-100)
   - Does the speech flow logically?
   - Are ideas connected or does it jump around?
   - Is there a clear structure?

3. **Vocabulary** (score 0-100)
   - Range and variety of words used
   - Repeated words that could be replaced
   - Good word choices worth noting

4. **Serious errors** (list them explicitly)
   - Errors that would confuse a native speaker
   - Fundamental grammar mistakes
   - Wrong word choices that change the meaning

## Output format

Respond ONLY with a valid JSON object. No markdown, no preamble. Example structure:

{
  "grammar_score": 72,
  "coherence_score": 68,
  "vocabulary_score": 65,
  "serious_errors_count": 3,
  "summary": "Brief overall impression in 2-3 sentences.",
  "grammar": {
    "score": 72,
    "errors": [
      {"original": "I was go to the store", "correction": "I went to the store", "explanation": "Past simple, not 'was + infinitive'"}
    ],
    "positive": ["Good use of present perfect in context"]
  },
  "coherence": {
    "score": 68,
    "issues": ["Topic shifted abruptly at minute 3 without transition"],
    "positive": ["Strong opening, clear introduction of the main idea"]
  },
  "vocabulary": {
    "score": 65,
    "repeated_words": ["thing (used 8 times) → consider: aspect, element, matter"],
    "good_choices": ["'nevertheless' used correctly"],
    "suggestions": ["Instead of 'very big', try 'enormous' or 'substantial'"]
  },
  "serious_errors": [
    {"error": "I have 25 years", "correction": "I am 25 years old", "why_serious": "This is a fundamental error that confuses native speakers"}
  ],
  "improvement_from_last": ""
}
"""


def _build_prompt(transcription: str, context: dict) -> str:
    sc = context["scorecard"]
    recent = context["recent_sessions"]
    mode = context["mode"]

    parts = [BASE_PROMPT]

    # Scorecard actual
    if sc.get("total_sessions", 0) > 0:
        parts.append("\n## Student progress so far\n")
        parts.append(scorecard_summary(sc))

    # Sesiones recientes
    if recent:
        label = "all sessions so far" if mode == "full" else f"last {len(recent)} sessions"
        parts.append(f"\n## Recent session reports ({label})\n")
        for s in recent[-3:]:  # máximo 3 sesiones en el prompt para no inflar
            parts.append(f"\n### Session {s['date']}")
            parts.append(f"Summary: {s.get('summary', 'N/A')}")
            parts.append(f"Scores — Grammar: {s.get('grammar_score')}, Coherence: {s.get('coherence_score')}, Vocabulary: {s.get('vocabulary_score')}")
            if s.get("serious_errors"):
                parts.append(f"Serious errors that session: {len(s.get('serious_errors', []))}")

    # Instrucción de continuidad
    if sc.get("total_sessions", 0) > 0:
        parts.append("\n## Important")
        parts.append(
            "Fill the 'improvement_from_last' field comparing this session to the previous one. "
            "Be specific: mention if recurring errors from before appear again or were fixed."
        )

    # Transcripción
    parts.append("\n## Today's transcription\n")
    parts.append(transcription)

    return "\n".join(parts)


def analyze(transcription: str) -> dict:
    """
    Recibe la transcripción y devuelve el reporte como dict.
    """
    print("  → Analizando con Claude...")
    context = build_context()
    prompt = _build_prompt(transcription, context)

    message = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Limpiamos por si el modelo pone backticks de todas formas
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude no devolvió JSON válido:\n{raw}\n\nError: {e}")

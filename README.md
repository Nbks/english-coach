# English Coach

A personal Python CLI tool to transcribe, analyze, and track your daily English-speaking practice videos. Records your progress over time with detailed AI feedback.

## Features

- **Video-to-Text**: Extracts audio from any MP4 and transcribes it using OpenAI Whisper
- **AI Analysis**: Claude (Anthropic) analyzes your speaking across 3 dimensions:
  - **Grammar** (0-100): Verb tenses, articles, prepositions, agreement
  - **Coherence** (0-100): Logical flow, structure, transitions
  - **Vocabulary** (0-100): Word variety, repetitions, good choices
- **Serious Errors Detection**: Flags mistakes that would confuse native speakers
- **Progress Tracking**: Maintains a rolling scorecard comparing session-to-session trends
- **Session Comparison**: Automatically compares each session to your previous one
- **Local Storage**: All data persisted as JSON files in `~/.english-coach/` (no database needed)
- **Adaptive Context**: First 9 days get full history context; day 10+ uses rolling 7-day window for Claude prompts

## Requirements

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/) binary installed and available on your system PATH
- API keys:
  - OpenAI API key (for Whisper transcription)
  - Anthropic API key (for Claude analysis)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Nbks/english-coach.git
cd english-coach
```

2. Install Python dependencies:
```bash
pip install openai anthropic typer rich ffmpeg-python
```

3. Set your API keys as environment variables:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Usage

### Process a daily speaking video

```bash
python cli.py run path/to/your/video.mp4
```

This will:
1. Extract audio and transcribe it
2. Send the transcription + your history to Claude for analysis
3. Save the session report and update your scorecard
4. Display the full report in the terminal

### Specify a different date

```bash
python cli.py run video.mp4 --date 2024-03-15
```

### View your overall progress

```bash
python cli.py stats
```

Shows your scorecard with all-time metrics and trends.

### View a specific session report

```bash
python cli.py show                    # today's session
python cli.py show 2024-03-15         # specific date
```

## Project Structure

```
english-coach/
├── cli.py                  # Typer CLI entry point (run, stats, show)
├── coach/
│   ├── transcriber.py      # Audio extraction (ffmpeg) + Whisper transcription
│   ├── analyzer.py         # Claude prompt builder and analysis
│   ├── storage.py          # JSON persistence in ~/.english-coach/
│   └── context.py          # Scorecard logic and context window management
└── README.md
```

## Data Storage

All data is stored locally in `~/.english-coach/`:

- `sessions/YYYY-MM-DD.json` — Individual session reports (transcript + analysis)
- `scorecard.json` — Rolling metrics and trends across all sessions
- `config.json` — User configuration (if needed)

## Example Output

```
English Coach — sesión 2024-03-15

✓ Transcripción lista (342 palabras)
✓ Análisis listo

────────────────── Reporte — 2024-03-15 ──────────────────
╭───────────── Resumen ─────────────╮
│ Buena fluidez general. Atención  │
│ a los tiempos verbales.          │
╰──────────────────────────────────╯

Métrica   Puntaje   Tendencia
────────  ────────  ─────────
Gramática 72/100    ↑+5
Coherencia 68/100  →+0
Vocabulario 65/100 ↓-3
```

## License

MIT

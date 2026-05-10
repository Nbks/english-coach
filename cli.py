from datetime import date
from pathlib import Path
from dotenv import load_dotenv

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from coach import transcriber, analyzer
from coach.context import update_scorecard, get_scorecard, scorecard_summary
from coach import storage


app = typer.Typer(help="English Coach — daily speaking practice analyzer")
console = Console()


# ── run ───────────────────────────────────────────────────────────────────────

@app.command()
def run(
    video: Path = typer.Argument(..., help="Path al video mp4 de hoy"),
    date_override: str = typer.Option(None, "--date", help="Fecha manual YYYY-MM-DD"),
):
    """Procesa el video del día: transcribe, analiza y guarda el reporte."""
    load_dotenv()
    session_date = date.fromisoformat(date_override) if date_override else date.today()

    console.print(f"\n[bold]English Coach[/bold] — sesión {session_date.isoformat()}\n")

    # 1. Transcribir
    with console.status("Transcribiendo..."):
        transcript = transcriber.transcribe(video)
    console.print(f"[green]✓[/green] Transcripción lista ({len(transcript.split())} palabras)\n")

    # 2. Analizar
    with console.status("Analizando con Claude..."):
        report = analyzer.analyze(transcript)
    console.print("[green]✓[/green] Análisis listo\n")

    # 3. Guardar sesión
    session_data = {
        **report,
        "transcript": transcript,
    }
    storage.save_session(session_data, session_date)

    # 4. Actualizar scorecard
    update_scorecard(report)

    # 5. Mostrar reporte
    _print_report(report, session_date)


# ── stats ─────────────────────────────────────────────────────────────────────

@app.command()
def stats():
    """Muestra el scorecard general de progreso."""
    sc = get_scorecard()
    if sc.get("total_sessions", 0) == 0:
        console.print("[yellow]Todavía no hay sesiones registradas.[/yellow]")
        raise typer.Exit()

    console.print(Panel(scorecard_summary(sc), title="Tu progreso", border_style="blue"))


# ── show ──────────────────────────────────────────────────────────────────────

@app.command()
def show(
    session_date: str = typer.Argument(None, help="Fecha YYYY-MM-DD (default: hoy)"),
):
    """Muestra el reporte de una sesión específica."""
    d = date.fromisoformat(session_date) if session_date else date.today()
    data = storage.load_session(d)
    if not data:
        console.print(f"[red]No hay sesión para {d.isoformat()}[/red]")
        raise typer.Exit(1)
    _print_report(data, d)


# ── helpers ───────────────────────────────────────────────────────────────────

def _print_report(report: dict, session_date: date):
    console.rule(f"Reporte — {session_date.isoformat()}")

    # Resumen
    if report.get("summary"):
        console.print(Panel(report["summary"], title="Resumen", border_style="cyan"))

    # Scores
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Métrica", style="dim")
    table.add_column("Puntaje", justify="center")
    table.add_column("Tendencia", justify="center")

    sc = get_scorecard().get("metrics", {})
    for key, label in [("grammar", "Gramática"), ("coherence", "Coherencia"), ("vocabulary", "Vocabulario")]:
        score = report.get(f"{key}_score", "—")
        trend = sc.get(key, {}).get("trend", 0)
        trend_str = f"[green]+{trend}[/green]" if trend > 0 else (f"[red]{trend}[/red]" if trend < 0 else "—")
        table.add_row(label, str(score), trend_str)

    console.print(table)

    # Errores graves
    serious = report.get("serious_errors", [])
    if serious:
        console.print(f"\n[bold red]Errores graves ({len(serious)})[/bold red]")
        for e in serious:
            console.print(f"  ✗ [red]{e.get('error')}[/red]")
            console.print(f"    → {e.get('correction')}")
            console.print(f"    [dim]{e.get('why_serious')}[/dim]\n")

    # Gramática
    grammar = report.get("grammar", {})
    if grammar.get("errors"):
        console.print("[bold]Errores de gramática[/bold]")
        for e in grammar["errors"][:5]:  # máximo 5 para no saturar
            console.print(f"  ✗ [yellow]{e.get('original')}[/yellow] → {e.get('correction')}")
            console.print(f"    [dim]{e.get('explanation')}[/dim]")

    # Mejora vs sesión anterior
    improvement = report.get("improvement_from_last", "")
    if improvement:
        console.print(Panel(improvement, title="Comparado con la sesión anterior", border_style="green"))

    console.print()


if __name__ == "__main__":
    app()

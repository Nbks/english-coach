import subprocess
import tempfile
from pathlib import Path

from openai import OpenAI



def extract_audio(video_path: Path) -> Path:
    client = OpenAI()
    """Extrae el audio del video a un .mp3 temporal usando ffmpeg."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    out_path = Path(tmp.name)

    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-vn",                   # sin video
            "-ar", "16000",          # 16kHz — suficiente para speech
            "-ac", "1",              # mono
            "-q:a", "4",
            str(out_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falló:\n{result.stderr}")

    return out_path


def transcribe(video_path: Path) -> str:
    """
    Recibe el path del video, extrae el audio y devuelve
    la transcripción cruda como string.
    """
    client = OpenAI()
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"No se encontró el video: {video_path}")

    print(f"  → Extrayendo audio de {video_path.name}...")
    audio_path = extract_audio(video_path)

    try:
        print("  → Transcribiendo con Whisper...")
        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en",       # forzamos inglés
                response_format="text",
            )
        return response.strip()
    finally:
        audio_path.unlink(missing_ok=True)  # limpiamos el temp

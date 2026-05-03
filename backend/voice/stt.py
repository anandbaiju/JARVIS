"""
Speech-to-Text using faster-whisper.
Records audio from the default Windows microphone and transcribes it.
"""

import tempfile
import wave
from pathlib import Path
from typing import Optional

import numpy as np

# Guard sounddevice import — mic may not be available
try:
    import sounddevice as sd
    _MIC_AVAILABLE = True
except (ImportError, OSError):
    sd = None  # type: ignore[assignment]
    _MIC_AVAILABLE = False

# Guard faster-whisper import — requires C++ redistributable on Windows
try:
    from faster_whisper import WhisperModel
    _WHISPER_MODEL: Optional[WhisperModel] = None
    _WHISPER_AVAILABLE = True
except ImportError:
    _WHISPER_AVAILABLE = False
    _WHISPER_MODEL = None


def _get_model() -> "WhisperModel":
    """Lazy-load the Whisper model on first use to avoid slow startup."""
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        _WHISPER_MODEL = WhisperModel("base", device="cpu", compute_type="int8")
    return _WHISPER_MODEL


def transcribe_audio(audio_path: str) -> str:
    """Transcribe a WAV file to text using faster-whisper.

    Args:
        audio_path: Absolute path to a WAV audio file.

    Returns:
        The transcribed text, or an error message if Whisper is unavailable.
    """
    if not _WHISPER_AVAILABLE:
        return "[STT unavailable — faster-whisper is not installed]"

    model = _get_model()
    segments, _ = model.transcribe(audio_path, beam_size=5)
    text = " ".join(seg.text.strip() for seg in segments)
    return text.strip() or "[No speech detected]"


def record_and_transcribe(duration: int = 5, sample_rate: int = 16000) -> str:
    """Record audio from the default mic, save to a temp WAV, and transcribe.

    Args:
        duration: Recording duration in seconds.
        sample_rate: Audio sample rate in Hz.

    Returns:
        Transcribed text from the recorded audio.
    """
    if not _MIC_AVAILABLE:
        return "[Microphone unavailable — sounddevice failed to initialise]"
    if not _WHISPER_AVAILABLE:
        return "[STT unavailable — faster-whisper is not installed]"

    # Record audio from the default input device
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    )
    sd.wait()  # Block until recording finishes

    # Write to a temporary WAV file in %TEMP%
    tmp_dir = Path(tempfile.gettempdir())
    tmp_path = tmp_dir / "jarvis_recording.wav"

    with wave.open(str(tmp_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())

    return transcribe_audio(str(tmp_path))


from functools import lru_cache
import io

import numpy as np
import soundfile as sf


MODEL_NAME = "openai/whisper-tiny"


@lru_cache(maxsize=1)
def get_transcriber():
    """Load Whisper Tiny only when transcription is requested."""
    from transformers import pipeline

    return pipeline(
        "automatic-speech-recognition",
        model=MODEL_NAME,
        device=-1,  # CPU
    )


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Convert uploaded audio into a transcript.
    Audio is converted to mono, 16 kHz before transcription.
    """
    try:
        audio, sample_rate = sf.read(
            io.BytesIO(audio_bytes),
            dtype="float32",
        )

        if audio.size == 0:
            raise ValueError("The uploaded audio is empty.")

        # Convert stereo audio to mono.
        if audio.ndim == 2:
            audio = np.mean(audio, axis=1)

        # Resample to 16 kHz if required.
        if sample_rate != 16000:
            import librosa

            audio = librosa.resample(
                audio,
                orig_sr=sample_rate,
                target_sr=16000,
            )

        result = get_transcriber()(
            {
                "raw": audio,
                "sampling_rate": 16000,
            }
        )

        transcript = result.get("text", "").strip()

        if not transcript:
            raise ValueError("No speech could be detected.")

        return transcript

    except Exception as exc:
        raise ValueError(
            f"Audio transcription failed: {exc}"
        ) from exc

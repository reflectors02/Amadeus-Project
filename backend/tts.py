import os
import hashlib
import platform
import shutil
import subprocess
import threading
from pathlib import Path

import requests

# Resolve paths from this file so the backend works regardless of cwd.
BACKEND_DIR = Path(__file__).resolve().parent
REF_WAV = BACKEND_DIR / "assets" / "reference_audio" / "kurisu10s.wav"
OUT_WAV = BACKEND_DIR / "generated" / "generated.wav"
REF_TXT = "ん? ほっと来てくれませんか?ん? ふざけてないでちょっと来てくださいアニカって何ですか?人激の悪い私は"

GPTSOVITS_API_URL = os.getenv("GPTSOVITS_API_URL", "http://127.0.0.1:9880")
STREAMING_MODE = int(os.getenv("GPTSOVITS_STREAMING_MODE", "1"))
_speech_lock = threading.Lock()


def _request_payload(text: str) -> dict:
    if not REF_WAV.exists():
        raise FileNotFoundError(f"Reference audio not found: {REF_WAV}")
    return {
        "text": text,
        "text_lang": "ja",
        "ref_audio_path": str(REF_WAV),
        "prompt_text": REF_TXT,
        "prompt_lang": "ja",
        "text_split_method": "cut5",
        "batch_size": 1,
        "batch_threshold": 0.75,
        "split_bucket": True,
        "speed_factor": 1.0,
        "fragment_interval": 0.15,
        "seed": -1,
        "media_type": "wav",
        "parallel_infer": True,
        "repetition_penalty": 1.35,
        "sample_steps": 16,
        "super_sampling": False,
        "streaming_mode": STREAMING_MODE,
        "overlap_length": 2,
        "min_chunk_length": 16,
    }


def _start_stream_player():
    """Start a player that accepts a WAV header followed by PCM bytes."""
    ffplay = shutil.which("ffplay")
    if ffplay:
        return subprocess.Popen(
            [ffplay, "-nodisp", "-autoexit", "-loglevel", "error", "-i", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    mpv = shutil.which("mpv")
    if mpv:
        return subprocess.Popen(
            [mpv, "--no-video", "--really-quiet", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    print("[AmadeusSpeak] No ffplay or mpv found; saving audio and playing after generation.")
    return None


def _finish_stream_player(player):
    if player is None:
        return
    try:
        if player.stdin:
            player.stdin.close()
        player.wait(timeout=30)
    except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
        try:
            player.kill()
        except OSError:
            pass


def _stream_audio(text: str, play: bool):
    OUT_WAV.parent.mkdir(parents=True, exist_ok=True)
    temp_path = OUT_WAV.with_suffix(".streaming.tmp")
    player = _start_stream_player() if play else None

    try:
        with requests.post(
            f"{GPTSOVITS_API_URL}/tts",
            json=_request_payload(text),
            stream=True,
            timeout=None,
        ) as response:
            response.raise_for_status()
            with temp_path.open("wb") as output:
                for chunk in response.iter_content(chunk_size=4096):
                    if not chunk:
                        continue
                    output.write(chunk)
                    if player is not None and player.stdin is not None:
                        try:
                            player.stdin.write(chunk)
                            player.stdin.flush()
                        except (BrokenPipeError, OSError):
                            _finish_stream_player(player)
                            player = None
        temp_path.replace(OUT_WAV)
    finally:
        _finish_stream_player(player)
        if temp_path.exists():
            temp_path.unlink()


def streamVoiceChunks(text: str, message_id: int | None = None, retention: int = 100):
    """Yield GPT-SoVITS WAV chunks for browser playback while saving a copy."""
    with _speech_lock:
        OUT_WAV.parent.mkdir(parents=True, exist_ok=True)
        cache_dir = OUT_WAV.parent / "voices"
        fingerprint = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        cached = cache_dir / f"{message_id}-{fingerprint}.wav" if message_id is not None else None
        if cached is not None and cached.exists():
            with cached.open("rb") as audio:
                while chunk := audio.read(4096):
                    yield chunk
            return
        if cached is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)
        temp_path = (cached.with_suffix(".tmp") if cached is not None
                     else OUT_WAV.with_suffix(".browser.tmp"))

        try:
            with requests.post(
                f"{GPTSOVITS_API_URL}/tts",
                json=_request_payload(text),
                stream=True,
                timeout=(10, 120),
            ) as response:
                response.raise_for_status()
                with temp_path.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=4096):
                        if not chunk:
                            continue
                        output.write(chunk)
                        yield chunk
            if cached is None:
                temp_path.replace(OUT_WAV)
            else:
                temp_path.replace(cached)
                # Preserve the legacy latest-recording copy for existing tools.
                shutil.copyfile(cached, OUT_WAV)
                recordings = sorted(cache_dir.glob("[0-9]*.wav"),
                                    key=lambda path: path.stat().st_mtime, reverse=True)
                for old in recordings[max(1, retention):]:
                    old.unlink(missing_ok=True)
        finally:
            if temp_path.exists():
                temp_path.unlink()


def streamVoice(text: str):
    """Stream native GPT-SoVITS audio directly to one continuous player."""
    with _speech_lock:
        _stream_audio(text, play=True)


def generateVoice(text: str):
    """Generate a complete WAV without starting playback."""
    with _speech_lock:
        _stream_audio(text, play=False)


def _play_wav_path(wav_path: Path):
    path = str(wav_path.resolve())
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["afplay", path], check=False)
        elif system == "Windows":
            subprocess.run([
                "powershell", "-NoProfile", "-Command",
                f'(New-Object Media.SoundPlayer "{path}").PlaySync();',
            ], check=False)
        else:
            for command in (
                ["paplay", path],
                ["aplay", path],
                ["ffplay", "-nodisp", "-autoexit", path],
            ):
                if shutil.which(command[0]):
                    subprocess.run(command, check=False)
                    break
    except Exception as error:
        print(f"[AmadeusSpeak] play_sound failed: {error}")


def play_sound():
    _play_wav_path(OUT_WAV)

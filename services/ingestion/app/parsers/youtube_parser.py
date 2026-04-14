import logging
import tempfile
from pathlib import Path

import yt_dlp

from .audio_parser import AudioParser

logger = logging.getLogger(__name__)


class YouTubeParser:
    """Download audio from a YouTube video and transcribe it via Deepgram."""

    def __init__(self, audio_parser: AudioParser):
        self._audio_parser = audio_parser

    def parse(self, url: str) -> dict:
        """
        Download audio from a YouTube URL, transcribe with Deepgram,
        and return the transcript with video metadata.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path, video_info = self._download_audio(url, tmpdir)
            logger.info(f"Downloaded audio: {audio_path.name} ({audio_path.stat().st_size} bytes)")

            result = self._audio_parser.parse(audio_path)

        result.setdefault("extra", {}).update({
            "youtube_url": url,
            "video_title": video_info.get("title", ""),
            "channel": video_info.get("channel", "") or video_info.get("uploader", ""),
            "video_duration_seconds": video_info.get("duration", 0),
        })

        return result, video_info

    @staticmethod
    def _download_audio(url: str, output_dir: str) -> tuple[Path, dict]:
        """Use yt-dlp to extract audio as WAV (16kHz mono) for Deepgram."""
        output_template = str(Path(output_dir) / "audio.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                },
                {
                    "key": "FFmpegMetadata",
                },
            ],
            "postprocessor_args": [
                "-ar", "16000",
                "-ac", "1",
            ],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        audio_file = Path(output_dir) / "audio.wav"
        if not audio_file.exists():
            candidates = list(Path(output_dir).glob("audio.*"))
            if not candidates:
                raise RuntimeError(f"yt-dlp did not produce an audio file for {url}")
            audio_file = candidates[0]

        return audio_file, info or {}

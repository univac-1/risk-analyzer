import os
import tempfile
import subprocess
from typing import Optional
from dataclasses import dataclass

from google.cloud import speech_v2 as speech
from google.cloud.speech_v2.types import cloud_speech

from app.config import get_settings
from app.services.storage import StorageService

settings = get_settings()


@dataclass
class TranscriptionSegment:
    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: float


@dataclass
class TranscriptionResult:
    segments: list[TranscriptionSegment]
    has_audio: bool


class AudioAnalyzerService:
    def __init__(self):
        self.storage_service = StorageService()
        self.speech_client = speech.SpeechClient()
        self.project_id = settings.google_cloud_project

    def extract_audio(self, video_path: str) -> Optional[str]:
        """
        動画から音声を抽出

        Args:
            video_path: ストレージ内の動画ファイルパス

        Returns:
            抽出された音声ファイルのローカルパス、音声がない場合はNone
        """
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
            video_local_path = video_file.name
            self.storage_service.download_file(video_path, video_local_path)

        audio_path = video_local_path.replace(".mp4", ".wav")

        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i", video_local_path,
                    "-vn",
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    "-y",
                    audio_path,
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                if "does not contain any stream" in result.stderr:
                    return None
                raise RuntimeError(f"ffmpeg error: {result.stderr}")

            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                return None

            return audio_path

        finally:
            if os.path.exists(video_local_path):
                os.unlink(video_local_path)

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        """
        音声を文字起こし

        Args:
            audio_path: 音声ファイルのローカルパス

        Returns:
            文字起こし結果
        """
        with open(audio_path, "rb") as audio_file:
            audio_content = audio_file.read()

        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["ja-JP"],
            model="chirp_2",
            features=cloud_speech.RecognitionFeatures(
                enable_word_time_offsets=True,
                enable_automatic_punctuation=True,
                diarization_config=cloud_speech.SpeakerDiarizationConfig(
                    min_speaker_count=1,
                    max_speaker_count=6,
                ),
            ),
        )

        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{self.project_id}/locations/us-central1/recognizers/_",
            config=config,
            content=audio_content,
        )

        try:
            response = self.speech_client.recognize(request=request)
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)

        segments = []
        for result in response.results:
            if not result.alternatives:
                continue

            alternative = result.alternatives[0]
            words = alternative.words if alternative.words else []

            if words:
                current_speaker = None
                current_text = []
                start_time = None

                for word in words:
                    speaker = f"Speaker {word.speaker_label}" if hasattr(word, 'speaker_label') else "Speaker 1"

                    if current_speaker is None:
                        current_speaker = speaker
                        start_time = word.start_offset.total_seconds()

                    if speaker != current_speaker:
                        segments.append(TranscriptionSegment(
                            speaker=current_speaker,
                            text=" ".join(current_text),
                            start_time=start_time,
                            end_time=word.start_offset.total_seconds(),
                            confidence=alternative.confidence,
                        ))
                        current_speaker = speaker
                        current_text = []
                        start_time = word.start_offset.total_seconds()

                    current_text.append(word.word)

                if current_text:
                    segments.append(TranscriptionSegment(
                        speaker=current_speaker,
                        text=" ".join(current_text),
                        start_time=start_time,
                        end_time=words[-1].end_offset.total_seconds() if words else start_time,
                        confidence=alternative.confidence,
                    ))
            else:
                segments.append(TranscriptionSegment(
                    speaker="Speaker 1",
                    text=alternative.transcript,
                    start_time=0.0,
                    end_time=0.0,
                    confidence=alternative.confidence,
                ))

        return TranscriptionResult(segments=segments, has_audio=len(segments) > 0)

    def analyze(self, video_path: str) -> TranscriptionResult:
        """
        動画から音声を解析

        Args:
            video_path: ストレージ内の動画ファイルパス

        Returns:
            文字起こし結果
        """
        audio_path = self.extract_audio(video_path)

        if audio_path is None:
            return TranscriptionResult(segments=[], has_audio=False)

        return self.transcribe(audio_path)

    def result_to_dict(self, result: TranscriptionResult) -> dict:
        """結果を辞書形式に変換"""
        return {
            "segments": [
                {
                    "speaker": seg.speaker,
                    "text": seg.text,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "confidence": seg.confidence,
                }
                for seg in result.segments
            ],
            "has_audio": result.has_audio,
        }

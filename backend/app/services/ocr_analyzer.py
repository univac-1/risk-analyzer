import os
import tempfile
from dataclasses import dataclass

from google.cloud import videointelligence_v1 as videointelligence

from app.services.storage import StorageService


@dataclass
class Vertex:
    x: float
    y: float


@dataclass
class BoundingBox:
    vertices: list[Vertex]


@dataclass
class TextAnnotation:
    text: str
    start_time: float
    end_time: float
    bounding_box: BoundingBox
    confidence: float


@dataclass
class OCRResult:
    text_annotations: list[TextAnnotation]
    has_text: bool


class OCRAnalyzerService:
    def __init__(self):
        self.storage_service = StorageService()
        self.video_client = videointelligence.VideoIntelligenceServiceClient()

    def analyze(self, video_path: str) -> OCRResult:
        """
        動画からテキストを抽出

        Args:
            video_path: ストレージ内の動画ファイルパス

        Returns:
            OCR結果
        """
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
            video_local_path = video_file.name
            self.storage_service.download_file(video_path, video_local_path)

        try:
            with open(video_local_path, "rb") as f:
                input_content = f.read()

            features = [videointelligence.Feature.TEXT_DETECTION]

            config = videointelligence.TextDetectionConfig(
                language_hints=["ja"]
            )

            video_context = videointelligence.VideoContext(
                text_detection_config=config
            )

            operation = self.video_client.annotate_video(
                request={
                    "features": features,
                    "input_content": input_content,
                    "video_context": video_context,
                }
            )

            result = operation.result(timeout=600)

        finally:
            if os.path.exists(video_local_path):
                os.unlink(video_local_path)

        annotations = []

        for annotation_result in result.annotation_results:
            for text_annotation in annotation_result.text_annotations:
                text = text_annotation.text

                for segment in text_annotation.segments:
                    start_time = segment.segment.start_time_offset.total_seconds()
                    end_time = segment.segment.end_time_offset.total_seconds()
                    confidence = segment.confidence

                    if segment.frames:
                        frame = segment.frames[0]
                        vertices = [
                            Vertex(
                                x=vertex.x if hasattr(vertex, 'x') else 0.0,
                                y=vertex.y if hasattr(vertex, 'y') else 0.0,
                            )
                            for vertex in frame.rotated_bounding_box.vertices
                        ]
                    else:
                        vertices = [Vertex(0, 0), Vertex(1, 0), Vertex(1, 1), Vertex(0, 1)]

                    annotations.append(TextAnnotation(
                        text=text,
                        start_time=start_time,
                        end_time=end_time,
                        bounding_box=BoundingBox(vertices=vertices),
                        confidence=confidence,
                    ))

        return OCRResult(
            text_annotations=annotations,
            has_text=len(annotations) > 0,
        )

    def result_to_dict(self, result: OCRResult) -> dict:
        """結果を辞書形式に変換"""
        return {
            "text_annotations": [
                {
                    "text": ann.text,
                    "start_time": ann.start_time,
                    "end_time": ann.end_time,
                    "bounding_box": {
                        "vertices": [
                            {"x": v.x, "y": v.y}
                            for v in ann.bounding_box.vertices
                        ]
                    },
                    "confidence": ann.confidence,
                }
                for ann in result.text_annotations
            ],
            "has_text": result.has_text,
        }

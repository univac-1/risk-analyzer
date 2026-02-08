from dataclasses import dataclass, asdict
from typing import Optional

from google.cloud import videointelligence

from app.config import get_settings

settings = get_settings()


@dataclass
class Vertex:
    x: float
    y: float


@dataclass
class BoundingBox:
    vertices: list[Vertex]


@dataclass
class TimestampedObject:
    bounding_box: BoundingBox
    time_offset: float


@dataclass
class TrackedObject:
    label: str
    confidence: float
    track_id: int
    segments: list[tuple[float, float]]
    frames: list[TimestampedObject]


@dataclass
class ExplicitContentAnnotation:
    time_offset: float
    likelihood: str


@dataclass
class VideoAnalysisResult:
    tracked_objects: list[TrackedObject]
    explicit_content_annotations: list[ExplicitContentAnnotation]


class VideoAnalyzerService:
    def __init__(self):
        self.video_client = videointelligence.VideoIntelligenceServiceClient()

    def analyze(self, video_path: str) -> Optional[VideoAnalysisResult]:
        """
        動画全体をVideo Intelligence APIで解析

        Args:
            video_path: ストレージ内の動画ファイルパス (object name)

        Returns:
            映像解析結果
        """
        gcs_uri = f"gs://{settings.google_cloud_storage_bucket}/{video_path}"
        features = [
            videointelligence.Feature.OBJECT_TRACKING,
            videointelligence.Feature.EXPLICIT_CONTENT_DETECTION,
        ]

        operation = self.video_client.annotate_video(
            request={"features": features, "input_uri": gcs_uri}
        )
        print(f"Waiting for video analysis operation for {gcs_uri} to complete...")
        result = operation.result(timeout=600)
        print("\nFinished video analysis.")

        tracked_objects = self._parse_object_tracking(result)
        explicit_annotations = self._parse_explicit_content(result)

        return VideoAnalysisResult(
            tracked_objects=tracked_objects,
            explicit_content_annotations=explicit_annotations,
        )

    def _parse_object_tracking(self, result) -> list[TrackedObject]:
        """オブジェクト追跡の結果をパース"""
        object_annotations = result.annotation_results[0].object_annotations
        tracked_objects = []

        for annotation in object_annotations:
            # The API returns a unique track_id for each object detected in a video.
            track_id = annotation.track_id
            label = annotation.entity.description
            confidence = annotation.confidence
            
            # Each segment represents a time range where the object is detected.
            segments = []
            for segment in annotation.segment:
                start_time = segment.start_time_offset.total_seconds()
                end_time = segment.end_time_offset.total_seconds()
                segments.append((start_time, end_time))

            # Each frame provides the object's bounding box at a specific timestamp.
            frames = []
            for frame in annotation.frames:
                box = frame.normalized_bounding_box
                time_offset = frame.time_offset.total_seconds()
                
                vertices = [
                    Vertex(v.x, v.y) for v in [box.left, box.top, box.right, box.bottom]
                ]
                
                # A common representation uses 4 vertices. Re-ordering for consistency.
                bounding_box = BoundingBox(vertices=[
                    Vertex(box.left, box.top),
                    Vertex(box.right, box.top),
                    Vertex(box.right, box.bottom),
                    Vertex(box.left, box.bottom),
                ])
                
                frames.append(TimestampedObject(
                    bounding_box=bounding_box,
                    time_offset=time_offset
                ))
            
            if frames:
                tracked_objects.append(TrackedObject(
                    label=label,
                    confidence=confidence,
                    track_id=track_id,
                    segments=segments,
                    frames=frames
                ))
                
        return tracked_objects

    def _parse_explicit_content(self, result) -> list[ExplicitContentAnnotation]:
        """不適切なコンテンツ検出の結果をパース"""
        explicit_annotations = result.annotation_results[0].explicit_annotation.frames
        annotations = []

        for frame in explicit_annotations:
            time_offset = frame.time_offset.total_seconds()
            likelihood = videointelligence.Likelihood(frame.pornography_likelihood).name
            annotations.append(
                ExplicitContentAnnotation(
                    time_offset=time_offset, likelihood=likelihood
                )
            )
        return annotations

    def result_to_dict(self, result: Optional[VideoAnalysisResult]) -> dict:
        """結果を辞書形式に変換"""
        if not result:
            return {"tracked_objects": [], "explicit_content_annotations": []}
        return asdict(result)
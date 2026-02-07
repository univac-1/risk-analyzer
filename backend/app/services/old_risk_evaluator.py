import os
import base64
import tempfile
import subprocess
from dataclasses import dataclass
import json

import vertexai
from vertexai.generative_models import GenerativeModel, Part

from app.config import get_settings
from app.services.storage import StorageService

settings = get_settings()


@dataclass
class Vertex:
    x: float
    y: float


@dataclass
class BoundingBox:
    vertices: list[Vertex]


@dataclass
class PersonAttributes:
    expression: str
    gesture: str
    attire: str


@dataclass
class PersonDetection:
    bounding_box: BoundingBox
    attributes: PersonAttributes


@dataclass
class ObjectDetection:
    label: str
    bounding_box: BoundingBox
    confidence: float


@dataclass
class SceneClassification:
    location: str
    atmosphere: str
    context: str


@dataclass
class FrameAnalysis:
    timestamp: float
    persons: list[PersonDetection]
    objects: list[ObjectDetection]
    scene: SceneClassification


@dataclass
class VideoAnalysisResult:
    frames: list[FrameAnalysis]


class VideoAnalyzerService:
    def __init__(self):
        self.storage_service = StorageService()
        if settings.google_cloud_project:
            vertexai.init(project=settings.google_cloud_project, location="us-central1")
        self.model = GenerativeModel("gemini-2.0-flash-001")

    def extract_frames(self, video_path: str, interval: float = 2.0) -> list[tuple[float, str]]:
        """
        動画からフレームを抽出

        Args:
            video_path: ストレージ内の動画ファイルパス
            interval: フレーム抽出間隔（秒）

        Returns:
            (タイムスタンプ, base64エンコード画像)のリスト
        """
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
            video_local_path = video_file.name
            self.storage_service.download_file(video_path, video_local_path)

        frames = []
        frame_dir = tempfile.mkdtemp()

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_local_path,
                ],
                capture_output=True,
                text=True,
            )
            duration = float(result.stdout.strip()) if result.stdout.strip() else 0

            subprocess.run(
                [
                    "ffmpeg",
                    "-i", video_local_path,
                    "-vf", f"fps=1/{interval}",
                    "-q:v", "2",
                    f"{frame_dir}/frame_%04d.jpg",
                ],
                capture_output=True,
                timeout=300,
            )

            frame_files = sorted([f for f in os.listdir(frame_dir) if f.endswith(".jpg")])

            for i, frame_file in enumerate(frame_files):
                frame_path = os.path.join(frame_dir, frame_file)
                timestamp = i * interval

                with open(frame_path, "rb") as f:
                    frame_data = base64.b64encode(f.read()).decode("utf-8")

                frames.append((timestamp, frame_data))
                os.unlink(frame_path)

        finally:
            if os.path.exists(video_local_path):
                os.unlink(video_local_path)
            if os.path.exists(frame_dir):
                os.rmdir(frame_dir)

        return frames

    def analyze_frame(self, timestamp: float, frame_base64: str) -> FrameAnalysis:
        """
        単一フレームを解析

        Args:
            timestamp: タイムスタンプ
            frame_base64: base64エンコードされた画像

        Returns:
            フレーム解析結果
        """
        prompt = """この画像を詳細に分析し、以下の情報をJSON形式で返してください：

1. persons: 画像内の人物リスト。各人物について:
   - expression: 表情（例: 笑顔, 真剣, 怒り, 悲しみ, 驚き, 無表情など）
   - gesture: ジェスチャー・動作（例: 手を振る, うなずく, 指差し, 腕組みなど）
   - attire: 服装の特徴（例: ビジネススーツ, カジュアル, 制服など）

2. objects: 検出された重要な物体リスト。各物体について:
   - label: 物体名
   - confidence: 確信度（0-1）

3. scene: シーン全体の分析
   - location: 場所（例: オフィス, 屋外, 店舗など）
   - atmosphere: 雰囲気（例: プロフェッショナル, カジュアル, 緊張感があるなど）
   - context: 状況の説明（何が行われているか）

レスポンスはJSONのみで、説明は不要です：
{
  "persons": [{"expression": "", "gesture": "", "attire": ""}],
  "objects": [{"label": "", "confidence": 0.0}],
  "scene": {"location": "", "atmosphere": "", "context": ""}
}"""

        image_part = Part.from_data(
            data=base64.b64decode(frame_base64),
            mime_type="image/jpeg",
        )

        response = self.model.generate_content([prompt, image_part])

        try:
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            data = json.loads(response_text)
        except (json.JSONDecodeError, AttributeError):
            data = {
                "persons": [],
                "objects": [],
                "scene": {"location": "不明", "atmosphere": "不明", "context": "解析失敗"}
            }

        persons = []
        for p in data.get("persons", []):
            persons.append(PersonDetection(
                bounding_box=BoundingBox(vertices=[
                    Vertex(0, 0), Vertex(1, 0), Vertex(1, 1), Vertex(0, 1)
                ]),
                attributes=PersonAttributes(
                    expression=p.get("expression", ""),
                    gesture=p.get("gesture", ""),
                    attire=p.get("attire", ""),
                ),
            ))

        objects = []
        for o in data.get("objects", []):
            objects.append(ObjectDetection(
                label=o.get("label", ""),
                bounding_box=BoundingBox(vertices=[
                    Vertex(0, 0), Vertex(1, 0), Vertex(1, 1), Vertex(0, 1)
                ]),
                confidence=o.get("confidence", 0.0),
            ))

        scene_data = data.get("scene", {})
        scene = SceneClassification(
            location=scene_data.get("location", ""),
            atmosphere=scene_data.get("atmosphere", ""),
            context=scene_data.get("context", ""),
        )

        return FrameAnalysis(
            timestamp=timestamp,
            persons=persons,
            objects=objects,
            scene=scene,
        )

    def analyze(self, video_path: str) -> VideoAnalysisResult:
        """
        動画全体を解析

        Args:
            video_path: ストレージ内の動画ファイルパス

        Returns:
            映像解析結果
        """
        frames_data = self.extract_frames(video_path)
        frame_analyses = []

        for timestamp, frame_base64 in frames_data:
            analysis = self.analyze_frame(timestamp, frame_base64)
            frame_analyses.append(analysis)

        return VideoAnalysisResult(frames=frame_analyses)

    def result_to_dict(self, result: VideoAnalysisResult) -> dict:
        """結果を辞書形式に変換"""
        return {
            "frames": [
                {
                    "timestamp": frame.timestamp,
                    "persons": [
                        {
                            "bounding_box": {
                                "vertices": [
                                    {"x": v.x, "y": v.y}
                                    for v in p.bounding_box.vertices
                                ]
                            },
                            "attributes": {
                                "expression": p.attributes.expression,
                                "gesture": p.attributes.gesture,
                                "attire": p.attributes.attire,
                            },
                        }
                        for p in frame.persons
                    ],
                    "objects": [
                        {
                            "label": o.label,
                            "bounding_box": {
                                "vertices": [
                                    {"x": v.x, "y": v.y}
                                    for v in o.bounding_box.vertices
                                ]
                            },
                            "confidence": o.confidence,
                        }
                        for o in frame.objects
                    ],
                    "scene": {
                        "location": frame.scene.location,
                        "atmosphere": frame.scene.atmosphere,
                        "context": frame.scene.context,
                    },
                }
                for frame in result.frames
            ]
        }
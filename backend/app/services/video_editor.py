"""FFmpeg-based video editing service for timeline editor."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable
import subprocess

from app.models.edit_session import EditAction, EditActionType

DEFAULT_FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


@dataclass
class FilterGraph:
    filter_complex: str | None
    video_map: str
    audio_map: str


class VideoEditorService:
    """Build FFmpeg filters and execute video editing commands."""

    def __init__(self, ffmpeg_path: str = "ffmpeg", font_path: str = DEFAULT_FONT_PATH) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.font_path = font_path

    def build_filter_graph(self, actions: Iterable[EditAction]) -> FilterGraph:
        filters: list[str] = []
        video_label = "0:v"
        audio_label = "0:a"
        audio_in_graph = False
        video_in_graph = False

        cut_actions = [action for action in actions if action.type == EditActionType.cut]
        if cut_actions:
            select_expr = self._build_between_expression(cut_actions, invert=True)
            filters.append(
                f"[0:v]select='{select_expr}',setpts=N/FRAME_RATE/TB[vcut]"
            )
            filters.append(
                f"[0:a]aselect='{select_expr}',asetpts=N/SR/TB[acut]"
            )
            video_label = "vcut"
            audio_label = "acut"
            audio_in_graph = True
            video_in_graph = True

        mute_actions = [action for action in actions if action.type == EditActionType.mute]
        for index, action in enumerate(mute_actions, start=1):
            next_label = f"a_mute_{index}"
            enable_expr = self._build_between_expression([action])
            filters.append(
                f"[{audio_label}]volume=0:enable='{enable_expr}'[{next_label}]"
            )
            audio_label = next_label
            audio_in_graph = True

        mosaic_actions = [action for action in actions if action.type == EditActionType.mosaic]
        for index, action in enumerate(mosaic_actions, start=1):
            options = action.options or {}
            x = int(options.get("x", 0))
            y = int(options.get("y", 0))
            width = int(options.get("width", 0))
            height = int(options.get("height", 0))
            blur_strength = int(options.get("blur_strength", options.get("blurStrength", 10)))
            enable_expr = self._build_between_expression([action])

            base_label = f"v_mosaic_base_{index}"
            blur_label = f"v_mosaic_blur_{index}"
            blurred_label = f"v_mosaic_blurred_{index}"
            next_label = f"v_mosaic_{index}"

            filters.append(f"[{video_label}]split=2[{base_label}][{blur_label}]")
            filters.append(
                f"[{blur_label}]crop={width}:{height}:{x}:{y},"
                f"boxblur={blur_strength}:1[{blurred_label}]"
            )
            filters.append(
                f"[{base_label}][{blurred_label}]overlay={x}:{y}:"
                f"enable='{enable_expr}'[{next_label}]"
            )
            video_label = next_label
            video_in_graph = True

        telop_actions = [action for action in actions if action.type == EditActionType.telop]
        for index, action in enumerate(telop_actions, start=1):
            options = action.options or {}
            text = self._escape_drawtext(str(options.get("text", "")))
            x = int(options.get("x", 0))
            y = int(options.get("y", 0))
            font_size = int(options.get("font_size", options.get("fontSize", 24)))
            font_color = str(options.get("font_color", options.get("fontColor", "#FFFFFF")))
            background_color = options.get("background_color", options.get("backgroundColor"))
            enable_expr = self._build_between_expression([action])

            drawtext = (
                f"drawtext=fontfile='{self.font_path}':text='{text}':"
                f"x={x}:y={y}:fontsize={font_size}:fontcolor={font_color}:"
                f"enable='{enable_expr}'"
            )
            if background_color:
                drawtext += f":box=1:boxcolor={background_color}"

            next_label = f"v_telop_{index}"
            filters.append(f"[{video_label}]{drawtext}[{next_label}]")
            video_label = next_label
            video_in_graph = True

        if not filters:
            return FilterGraph(filter_complex=None, video_map="0:v", audio_map="0:a")

        video_map = f"[{video_label}]" if video_in_graph else "0:v"
        audio_map = f"[{audio_label}]" if audio_in_graph else "0:a"
        return FilterGraph(filter_complex=";".join(filters), video_map=video_map, audio_map=audio_map)

    def run_ffmpeg(
        self,
        input_path: str,
        output_path: str,
        actions: Iterable[EditAction],
        on_progress: Callable[[float], None] | None = None,
        total_frames: int | None = None,
        duration_seconds: float | None = None,
    ) -> None:
        graph = self.build_filter_graph(actions)

        command = [self.ffmpeg_path, "-y", "-i", input_path]
        if graph.filter_complex:
            command += [
                "-filter_complex",
                graph.filter_complex,
                "-map",
                graph.video_map,
                "-map",
                graph.audio_map,
            ]
        else:
            command += ["-c", "copy"]

        command += ["-progress", "pipe:1", "-nostats", output_path]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if process.stdout:
            for line in process.stdout:
                progress = self._parse_progress_line(
                    line.strip(),
                    total_frames=total_frames,
                    duration_seconds=duration_seconds,
                )
                if progress is not None and on_progress:
                    on_progress(progress)

        process.wait()
        stderr_output = process.stderr.read() if process.stderr else ""
        if process.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {stderr_output}")

    @staticmethod
    def _parse_progress_line(
        line: str,
        total_frames: int | None,
        duration_seconds: float | None,
    ) -> float | None:
        if line.startswith("frame=") and total_frames:
            frame = int(line.split("=", 1)[1].strip())
            return min(frame / total_frames * 100.0, 100.0)
        if line.startswith("out_time_ms=") and duration_seconds:
            out_time_ms = int(line.split("=", 1)[1].strip())
            return min(out_time_ms / (duration_seconds * 1000) * 100.0, 100.0)
        return None

    @staticmethod
    def _build_between_expression(
        actions: Iterable[EditAction],
        invert: bool = False,
    ) -> str:
        ranges = [
            f"between(t,{action.start_time:.3f},{action.end_time:.3f})"
            for action in actions
        ]
        if not ranges:
            return "1" if invert else "0"
        expr = ranges[0] if len(ranges) == 1 else "+".join(ranges)
        return f"not({expr})" if invert else expr

    @staticmethod
    def _escape_drawtext(text: str) -> str:
        return (
            text.replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "\\'")
            .replace("\n", "\\n")
        )

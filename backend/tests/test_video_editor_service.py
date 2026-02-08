from uuid import uuid4

from app.models.edit_session import EditAction, EditActionType
from app.services.video_editor import VideoEditorService


def make_action(action_type, start, end, options=None):
    return EditAction(
        id=uuid4(),
        session_id=uuid4(),
        type=action_type,
        start_time=start,
        end_time=end,
        options=options,
    )


def test_build_filter_graph_empty():
    service = VideoEditorService()
    graph = service.build_filter_graph([])

    assert graph.filter_complex is None
    assert graph.video_map == "0:v"
    assert graph.audio_map == "0:a"


def test_build_filter_graph_ordering():
    service = VideoEditorService()
    actions = [
        make_action(EditActionType.cut, 5.0, 10.0),
        make_action(EditActionType.mute, 12.0, 15.0),
        make_action(
            EditActionType.telop,
            20.0,
            25.0,
            options={
                "text": "Test",
                "x": 10,
                "y": 20,
                "font_size": 24,
                "font_color": "#FFFFFF",
            },
        ),
    ]

    graph = service.build_filter_graph(actions)
    assert graph.filter_complex is not None

    filter_text = graph.filter_complex
    assert "select=" in filter_text
    assert "volume=0" in filter_text
    assert "drawtext=" in filter_text
    assert filter_text.index("select=") < filter_text.index("volume=0")
    assert filter_text.index("volume=0") < filter_text.index("drawtext=")


def test_build_filter_graph_mosaic():
    service = VideoEditorService()
    actions = [
        make_action(
            EditActionType.mosaic,
            3.0,
            6.0,
            options={"x": 5, "y": 6, "width": 120, "height": 80, "blur_strength": 8},
        )
    ]

    graph = service.build_filter_graph(actions)
    assert graph.filter_complex is not None
    assert "boxblur=" in graph.filter_complex
    assert "overlay=" in graph.filter_complex


def test_escape_drawtext():
    text = "Test: 'quote' \\ path"
    escaped = VideoEditorService._escape_drawtext(text)
    assert "\\:" in escaped
    assert "\\'" in escaped
    assert "\\\\" in escaped

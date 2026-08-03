from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from dvre.core.builder.utils.base_layer import (
    _fill_compound_gaps,
    process_base_layer,
)
from dvre.core.builder.utils.fusion_layer import process_fusion_layer
from dvre.core.builder.utils.layers import (
    compound_layer,
    load_previous_compound,
    process_layer,
)
from dvre.core.builder.utils.runtime import BuildRuntime
from dvre.schemas.clips import AudioClip, FusionSegment, VideoClip
from dvre.schemas.layers import BaseLayer, FusionLayer
from dvre.utils.errors import ResolveError
from dvre.utils.types import AUDIO_ONLY, VIDEO_ONLY


def _make_segment(start: int, end: int) -> FusionSegment:
    return FusionSegment(
        start_frame=start, end_frame=end, composition="Composition { }"
    )


def make_runtime(**overrides) -> BuildRuntime:
    runtime = BuildRuntime(
        project_service=MagicMock(),
        media_service=MagicMock(),
        timeline_service=MagicMock(),
        fusion_service=MagicMock(),
        video_validator=MagicMock(),
        audio_validator=MagicMock(),
    )
    for key, value in overrides.items():
        setattr(runtime, key, value)
    return runtime


class TestLoadPreviousCompound:
    def test_noop_without_previous_compound(self):
        runtime = make_runtime()
        load_previous_compound(runtime, "Layer1")
        runtime.timeline_service.get_compound_info.assert_not_called()
        runtime.timeline_service.delete_clips.assert_not_called()

    def test_loads_and_deletes_previous(self):
        runtime = make_runtime(prev_compound="compound")
        runtime.timeline_service.get_compound_info.return_value = (
            "mpi",
            10,
            100,
        )

        load_previous_compound(runtime, "Layer1")

        runtime.timeline_service.get_compound_info.assert_called_once_with("compound")
        runtime.timeline_service.delete_clips.assert_called_once_with(["compound"])
        assert runtime.compound_mpi == "mpi"
        assert runtime.compound_start == 10
        assert runtime.compound_end == 100


class TestCompoundLayer:
    def test_creates_compound(self):
        runtime = make_runtime()
        runtime.timeline_service.compound_clip.return_value = "compound_item"

        compound_layer(runtime, "Layer1")

        info = runtime.timeline_service.compound_clip.call_args.args[0]
        assert info == {"startTimecode": None, "name": "Layer1"}
        assert runtime.prev_compound == "compound_item"


class TestProcessLayer:
    def test_base_layer_dispatches(self):
        runtime = make_runtime()
        layer = BaseLayer(name="Base")

        with patch("dvre.core.builder.utils.layers.process_base_layer") as mock_process:
            process_layer(runtime, layer)
            mock_process.assert_called_once_with(runtime, layer)

    def test_fusion_layer_dispatches(self):
        runtime = make_runtime()
        layer = FusionLayer(name="Fusion", fusion_segments=[_make_segment(0, 100)])

        with patch(
            "dvre.core.builder.utils.layers.process_fusion_layer"
        ) as mock_process:
            process_layer(runtime, layer)
            mock_process.assert_called_once_with(runtime, layer)


class TestProcessBaseLayer:
    def test_ensure_track_counts(self):
        runtime = make_runtime()
        runtime.media_service.import_media.return_value = "media_item"
        layer = BaseLayer(
            name="Base",
            video_clips=[
                VideoClip(
                    path="v.mp4",
                    track=2,
                    start_frame=0,
                    end_frame=50,
                    timeline_start_frame=0,
                )
            ],
            audio_clips=[
                AudioClip(
                    path="a.wav",
                    track=1,
                    start_frame=0,
                    end_frame=50,
                    timeline_start_frame=0,
                )
            ],
        )

        process_base_layer(runtime, layer)

        calls = [
            c.args for c in runtime.timeline_service.ensure_track_count.call_args_list
        ]
        assert ("video", 2) in calls
        assert ("audio", 1) in calls
        runtime.media_service.import_media.assert_any_call(
            "v.mp4", runtime.video_validator
        )
        runtime.media_service.import_media.assert_any_call(
            "a.wav", runtime.audio_validator
        )

    def test_no_clips(self):
        runtime = make_runtime()
        layer = BaseLayer(name="Empty")

        process_base_layer(runtime, layer)

        runtime.timeline_service.ensure_track_count.assert_not_called()
        runtime.media_service.import_media.assert_not_called()


class TestFillCompoundGaps:
    def _clip(self, track, timeline_start, src_start=0, src_end=50):
        clip = MagicMock()
        clip.track = track
        clip.timeline_start_frame = timeline_start
        clip.end_frame = src_end
        clip.start_frame = src_start
        return clip

    def test_no_clips_fills_entire_range(self):
        runtime = make_runtime(compound_mpi="mpi", compound_start=0, compound_end=200)
        _fill_compound_gaps(runtime, [], VIDEO_ONLY)
        runtime.timeline_service.place_clip.assert_called_once_with(
            "mpi", 1, 0, 200, 0, VIDEO_ONLY
        )

    def test_clip_covering_full_range_no_fills(self):
        runtime = make_runtime(compound_mpi="mpi", compound_start=0, compound_end=100)
        clips = [self._clip(1, 0, src_end=100)]

        _fill_compound_gaps(runtime, clips, VIDEO_ONLY)

        runtime.timeline_service.place_clip.assert_not_called()

    def test_leading_and_trailing_gaps(self):
        runtime = make_runtime(compound_mpi="mpi", compound_start=0, compound_end=300)
        clips = [self._clip(1, 100)]

        _fill_compound_gaps(runtime, clips, VIDEO_ONLY)

        calls = [c.args for c in runtime.timeline_service.place_clip.call_args_list]
        assert ("mpi", 1, 0, 100, 0, VIDEO_ONLY) in calls  # leading gap
        assert ("mpi", 1, 150, 300, 150, VIDEO_ONLY) in calls  # trailing gap

    def test_fills_gap_between_clips(self):
        runtime = make_runtime(compound_mpi="mpi", compound_start=0, compound_end=400)
        clips = [
            self._clip(1, 100),
            self._clip(1, 200),
        ]

        _fill_compound_gaps(runtime, clips, VIDEO_ONLY)

        calls = [c.args for c in runtime.timeline_service.place_clip.call_args_list]
        assert ("mpi", 1, 0, 100, 0, VIDEO_ONLY) in calls
        assert ("mpi", 1, 150, 200, 150, VIDEO_ONLY) in calls  # between clips
        assert ("mpi", 1, 250, 400, 250, VIDEO_ONLY) in calls

    def test_ignores_non_track_one_clips(self):
        runtime = make_runtime(compound_mpi="mpi", compound_start=0, compound_end=200)
        clips = [self._clip(2, 50)]

        _fill_compound_gaps(runtime, clips, VIDEO_ONLY)

        runtime.timeline_service.place_clip.assert_called_once_with(
            "mpi", 1, 0, 200, 0, VIDEO_ONLY
        )

    def test_noop_without_compound(self):
        runtime = make_runtime()
        _fill_compound_gaps(runtime, [self._clip(1, 0)], VIDEO_ONLY)
        runtime.timeline_service.place_clip.assert_not_called()

    def test_uses_audio_type(self):
        runtime = make_runtime(compound_mpi="mpi", compound_start=0, compound_end=100)
        _fill_compound_gaps(runtime, [self._clip(1, 50)], AUDIO_ONLY)
        calls = [c.args for c in runtime.timeline_service.place_clip.call_args_list]
        assert ("mpi", 1, 0, 50, 0, AUDIO_ONLY) in calls


class TestProcessFusionLayer:
    def test_requires_previous_compound(self):
        runtime = make_runtime()
        layer = FusionLayer(name="Fusion", fusion_segments=[_make_segment(0, 100)])

        with pytest.raises(ResolveError):
            process_fusion_layer(runtime, layer)

    def test_places_segments_and_audio(self):
        runtime = make_runtime(compound_mpi="mpi", compound_start=0, compound_end=200)
        runtime.timeline_service.place_clip.return_value = "item"
        layer = FusionLayer(name="Fusion", fusion_segments=[_make_segment(50, 150)])

        process_fusion_layer(runtime, layer)

        calls = [c.args for c in runtime.timeline_service.place_clip.call_args_list]
        assert ("mpi", 1, 0, 50, 0, VIDEO_ONLY) in calls  # leading gap
        assert ("mpi", 1, 50, 150, 50, VIDEO_ONLY) in calls  # segment base
        assert ("mpi", 1, 150, 200, 150, VIDEO_ONLY) in calls  # trailing gap
        assert ("mpi", 1, 0, 200, 0, AUDIO_ONLY) in calls  # audio pass
        runtime.fusion_service.create_fusion_segment.assert_called_once_with(
            layer.fusion_segments[0], ["item"]
        )

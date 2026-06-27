from __future__ import annotations

import pytest
from pydantic import ValidationError

from dvre.schemas.api import BuildConfig, TimelineSettings
from dvre.schemas.clips import AudioClip, FusionSegment, VideoClip
from dvre.schemas.layers import BaseLayer, FusionLayer


class TestTimelineSettings:
    def test_defaults(self):
        settings = TimelineSettings()
        assert settings.width == 1920
        assert settings.height == 1080
        assert settings.frame_rate == 60.0
        assert settings.super_scale is None

    def test_custom_values(self):
        settings = TimelineSettings(
            width=3840, height=2160, frame_rate=29.97, super_scale=2
        )
        assert settings.width == 3840
        assert settings.height == 2160
        assert settings.frame_rate == 29.97
        assert settings.super_scale == 2

    @pytest.mark.parametrize("width", [0, -1])
    def test_invalid_width(self, width):
        with pytest.raises(ValidationError):
            TimelineSettings(width=width)

    @pytest.mark.parametrize("super_scale", [-1, 5])
    def test_invalid_super_scale(self, super_scale):
        with pytest.raises(ValidationError):
            TimelineSettings(super_scale=super_scale)


class TestVideoClip:
    def test_minimal(self):
        clip = VideoClip(
            path=r"C:\test.mp4", timeline_start_frame=0, start_frame=0, end_frame=100
        )
        assert clip.track == 1

    def test_invalid_track(self):
        with pytest.raises(ValidationError):
            VideoClip(
                path=r"C:\test.mp4",
                track=0,
                timeline_start_frame=0,
                start_frame=0,
                end_frame=100,
            )

    def test_negative_frames(self):
        with pytest.raises(ValidationError):
            VideoClip(
                path=r"C:\test.mp4",
                timeline_start_frame=-1,
                start_frame=0,
                end_frame=100,
            )


class TestAudioClip:
    def test_minimal(self):
        clip = AudioClip(
            path=r"C:\test.wav", timeline_start_frame=0, start_frame=0, end_frame=100
        )
        assert clip.track == 1


class TestFusionSegment:
    def test_minimal(self):
        clip = FusionSegment(start_frame=0, end_frame=100, comp_path=r"C:\test.comp")
        assert clip.start_frame == 0
        assert clip.end_frame == 100


class TestBaseLayer:
    def test_defaults(self):
        layer = BaseLayer(name="Test")
        assert layer.video_clips == []
        assert layer.audio_clips == []

    def test_with_clips(self, video_clips, audio_clips):
        layer = BaseLayer(name="Test", video_clips=video_clips, audio_clips=audio_clips)
        assert len(layer.video_clips) == 2
        assert len(layer.audio_clips) == 1


class TestFusionLayer:
    def test_requires_fusion_segments(self, fusion_segments):
        layer = FusionLayer(name="Test", fusion_segments=fusion_segments)
        assert len(layer.fusion_segments) == 1

    def test_empty_fusion_segments_fails(self):
        with pytest.raises(ValidationError):
            FusionLayer(name="Test", fusion_segments=[])


class TestBuildConfig:
    def test_minimal(self):
        config = BuildConfig(
            project_name="Test",
            timeline_name="Test",
            export_path=r"C:\output.mp4",
        )
        assert config.save_project is True
        assert config.layers == []

    def test_full_config(self, build_config):
        assert build_config.project_name == "Test Project"
        assert build_config.timeline_name == "Test Timeline"
        assert len(build_config.layers) == 1
        assert isinstance(build_config.layers[0], BaseLayer)

    def test_project_name_required(self):
        with pytest.raises(ValidationError):
            BuildConfig(timeline_name="Test", export_path=r"C:\output.mp4")

    def test_export_path_required(self):
        with pytest.raises(ValidationError):
            BuildConfig(project_name="Test", timeline_name="Test")

    def test_serialization_roundtrip(self, build_config):
        data = build_config.model_dump(mode="json")
        restored = BuildConfig.model_validate(data)
        assert restored.project_name == build_config.project_name
        assert restored.timeline_name == build_config.timeline_name
        assert restored.export_path == build_config.export_path
        assert restored.settings.width == build_config.settings.width

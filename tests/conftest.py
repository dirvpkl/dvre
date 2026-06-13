from __future__ import annotations
from pathlib import Path

import pytest

from dvre.schemas.api import BuildConfig, TimelineSettings
from dvre.schemas.clips import AudioClip, FusionClip, VideoClip
from dvre.schemas.layers import BaseLayer, FusionLayer

TEST_MEDIA = Path(__file__).parent.parent / "test_media"


@pytest.fixture
def timeline_settings() -> TimelineSettings:
    return TimelineSettings(width=1920, height=1080, frame_rate=25.0)


@pytest.fixture
def video_clips() -> list[VideoClip]:
    return [
        VideoClip(
            path=str(TEST_MEDIA / "clip1.mp4"),
            track=1,
            timeline_start_frame=0,
            start_frame=0,
            end_frame=100,
        ),
        VideoClip(
            path=str(TEST_MEDIA / "clip2.mp4"),
            track=1,
            timeline_start_frame=100,
            start_frame=0,
            end_frame=150,
        ),
    ]


@pytest.fixture
def audio_clips() -> list[AudioClip]:
    return [
        AudioClip(
            path=str(TEST_MEDIA / "audio.wav"),
            track=1,
            timeline_start_frame=0,
            start_frame=0,
            end_frame=250,
        ),
    ]


@pytest.fixture
def fusion_clips() -> list[FusionClip]:
    return [
        FusionClip(
            start_frame=50,
            end_frame=150,
            comp_path=str(TEST_MEDIA / "effect.comp"),
        ),
    ]


@pytest.fixture
def base_layer(video_clips, audio_clips) -> BaseLayer:
    return BaseLayer(
        name="Background",
        video_clips=video_clips,
        audio_clips=audio_clips,
    )


@pytest.fixture
def fusion_layer(fusion_clips) -> FusionLayer:
    return FusionLayer(
        name="Effects",
        fusion_clips=fusion_clips,
    )


@pytest.fixture
def build_config(timeline_settings, base_layer) -> BuildConfig:
    return BuildConfig(
        project_name="Test Project",
        timeline_name="Test Timeline",
        settings=timeline_settings,
        layers=[base_layer],
        export_path=str(TEST_MEDIA / "output.mp4"),
        save_project=False,
    )


@pytest.fixture
def build_config_with_fusion(timeline_settings, base_layer, fusion_layer) -> BuildConfig:
    return BuildConfig(
        project_name="Test Project Fusion",
        timeline_name="Test Timeline Fusion",
        settings=timeline_settings,
        layers=[base_layer, fusion_layer],
        export_path=str(TEST_MEDIA / "output_fusion.mp4"),
        save_project=False,
    )

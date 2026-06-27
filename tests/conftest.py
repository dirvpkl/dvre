from __future__ import annotations

from pathlib import Path

import pytest

from dvre.schemas.api import BuildConfig, TimelineSettings
from dvre.schemas.clips import AudioClip, FusionSegment, VideoClip
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
def fusion_segments() -> list[FusionSegment]:
    return [
        FusionSegment(
            start_frame=50,
            end_frame=150,
            composition="""Composition {
	CurrentTime = 1010,
	RenderRange = { 0, 965 },
	GlobalRange = { -2776, 385533 },
	CurrentID = 4,
	HiQ = true,
	PlaybackUpdateMode = 0,
	StereoMode = false,
	Version = "DaVinci Resolve Studio 21.0.0.0047",
	SavedOutputs = 0,
	HeldTools = 0,
	DisabledTools = 0,
	LockedTools = 0,
	AudioOffset = 0,
	Resumable = true,
	OutputClips = {
	},
	Tools = {
		MediaIn1 = Loader {
			ExtentSet = true,
			CustomData = {
				MediaProps = {
					MEDIA_AUDIO_TRACKS_DESC = {
						{
							MEDIA_AUDIO_BIT_DEPTH = 32,
							MEDIA_AUDIO_FRAME_RATE = 59.9400599400599,
							MEDIA_AUDIO_NUM_CHANNELS = 2,
							MEDIA_AUDIO_SAMPLE_RATE = 48000,
							MEDIA_AUDIO_START_TIME = 0,
							MEDIA_AUDIO_TRACK_ID = "Timeline Audio",
							MEDIA_AUDIO_TRACK_NAME = "Timeline Audio [Timeline 1]"
						},
						{
							MEDIA_AUDIO_BIT_DEPTH = 32,
							MEDIA_AUDIO_FRAME_RATE = 59.9400599400599,
							MEDIA_AUDIO_NUM_CHANNELS = 2,
							MEDIA_AUDIO_SAMPLE_RATE = 48000,
							MEDIA_AUDIO_START_TIME = 0,
							MEDIA_AUDIO_TRACK_ID = "123",
							MEDIA_AUDIO_TRACK_NAME = "pass.mp4"
						}
					},
					MEDIA_AUDIO_TRACKS_NUM = 2,
					MEDIA_FORMAT_TYPE = "QuickTime",
					MEDIA_HAS_AUDIO = true,
					MEDIA_HEIGHT = 1440,
					MEDIA_ID = "123",
					MEDIA_IS_SOURCE_RES = true,
					MEDIA_MARK_IN = 0,
					MEDIA_MARK_OUT = 965,
					MEDIA_NAME = "pass.mp4",
					MEDIA_NUM_FRAMES = 388310,
					MEDIA_NUM_LAYERS = 1,
					MEDIA_PAR = 1,
					MEDIA_PATH = "pass",
					MEDIA_SRC_FRAME_RATE = 59.9400599400599,
					MEDIA_START_FRAME = -2776,
					MEDIA_WIDTH = 2560
				},
			},
			Inputs = {
				GlobalIn = Input { Value = -2776, },
				GlobalOut = Input { Value = 385533, },
				AudioTrack = Input { Value = FuID { "Timeline Audio" }, },
				Layer = Input { Value = "0", },
				ClipTimeStart = Input { Value = -2776, },
				ClipTimeEnd = Input { Value = 385533, },
				["Gamut.SLogVersion"] = Input { Value = FuID { "SLog2" }, },
				DeepOutputMode = Input {
					Value = 0,
					Disabled = true,
				},
			},
			ViewInfo = OperatorInfo { Pos = { 55, 49.5 } },
			Version = 1,
			Clips = {
				Clip {
					ID = "Clip1",
					Multiframe = true,
					Filename = "pass",
					Length = 388310,
					LengthSetManually = true,
					GlobalStart = -2776,
					GlobalEnd = 385533,
					TrimIn = -2776,
					TrimOut = 385533,
				}
			}
		},
		Glow1 = Glow {
			CtrlWZoom = false,
			Inputs = {
				Blend = Input { Value = 0.2, },
				Filter = Input { Value = FuID { "Fast Gaussian" }, },
				Input = Input {
					SourceOp = "MediaIn1",
					Source = "Output",
				}
			},
			ViewInfo = OperatorInfo { Pos = { 165, 49.5 } },
		},
		MediaOut1 = Saver {
			Inputs = {
				Index = Input { Value = "0", },
				Input = Input {
					SourceOp = "Glow1",
					Source = "Output",
				}
			},
			ViewInfo = OperatorInfo { Pos = { 605, 49.5 } },
		}
	}
            }""",
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
def fusion_layer(fusion_segments) -> FusionLayer:
    return FusionLayer(
        name="Effects",
        fusion_segments=fusion_segments,
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
def build_config_with_fusion(
    timeline_settings, base_layer, fusion_layer
) -> BuildConfig:
    return BuildConfig(
        project_name="Test Project Fusion",
        timeline_name="Test Timeline Fusion",
        settings=timeline_settings,
        layers=[base_layer, fusion_layer],
        export_path=str(TEST_MEDIA / "output_fusion.mp4"),
        save_project=False,
    )

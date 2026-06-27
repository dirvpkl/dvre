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
        clip = FusionSegment(
            start_frame=0,
            end_frame=100,
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
        )
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

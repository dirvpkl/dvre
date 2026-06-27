from __future__ import annotations

import json

from dvre.schemas.api import BuildConfig
from dvre.schemas.clips import AudioClip, FusionSegment, VideoClip
from dvre.schemas.layers import BaseLayer, FusionLayer


class TestBuildConfigJSON:
    """Verify JSON serialization matches the API contract."""

    def test_build_config_to_json(self, build_config):
        data = build_config.model_dump(mode="json")
        assert data["project_name"] == "Test Project"
        assert data["timeline_name"] == "Test Timeline"
        assert data["export_path"].endswith("output.mp4")
        assert data["save_project"] is False
        assert data["settings"]["width"] == 1920
        assert data["settings"]["height"] == 1080
        assert data["settings"]["frame_rate"] == 25.0

    def test_build_config_with_fusion_to_json(self, build_config_with_fusion):
        data = build_config_with_fusion.model_dump(mode="json")
        assert len(data["layers"]) == 2
        assert data["layers"][0]["name"] == "Background"
        assert data["layers"][1]["name"] == "Effects"

        fusion_segments = data["layers"][1]["fusion_segments"]
        assert len(fusion_segments) == 1
        assert fusion_segments[0]["start_frame"] == 50
        assert fusion_segments[0]["end_frame"] == 150

    def test_roundtrip_via_json_string(self, build_config_with_fusion):
        json_str = build_config_with_fusion.model_dump_json(indent=2)
        parsed = json.loads(json_str)
        restored = BuildConfig.model_validate(parsed)

        assert restored.project_name == build_config_with_fusion.project_name
        assert len(restored.layers) == 2
        assert isinstance(restored.layers[0], BaseLayer)
        assert isinstance(restored.layers[1], FusionLayer)
        assert isinstance(restored.layers[0].video_clips[0], VideoClip)
        assert isinstance(restored.layers[0].audio_clips[0], AudioClip)
        assert isinstance(restored.layers[1].fusion_segments[0], FusionSegment)

    def test_json_structure_documentation(self, build_config_with_fusion):
        """Show the JSON structure — useful for API docs."""
        json_str = build_config_with_fusion.model_dump_json(indent=2)
        print(f"\n{build_config_with_fusion.project_name} JSON:\n{json_str}")

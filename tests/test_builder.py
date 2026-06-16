from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from dvre.core.builder.builder import OutputBuilder
from dvre.schemas.api import BuildConfig
from dvre.utils.errors import ResolveError


class TestOutputBuilder:
    """Tests for OutputBuilder — limited without DaVinci Resolve running."""

    def test_init(self):
        pm = MagicMock()
        builder = OutputBuilder(pm)
        assert builder.factory is not None

    def test_build_no_project_manager(self, build_config):
        with pytest.raises(Exception):
            OutputBuilder(None).build(build_config)

    def test_build_with_mock_project_manager(self, build_config):
        pm = MagicMock()
        builder = OutputBuilder(pm)

        with (
            patch("dvre.core.builder.builder.ProjectService") as mock_ps,
            patch("dvre.core.builder.builder.MediaService") as mock_ms,
            patch("dvre.core.builder.builder.TimelineService") as mock_ts,
            patch("dvre.core.builder.builder.FusionService") as mock_fs,
        ):
            mock_ps_instance = mock_ps.return_value
            mock_ps_instance.export_project.return_value = "job_123"

            result = builder.build(build_config)
            assert result == "job_123"
            mock_ps_instance.save_current_project.assert_not_called()


class TestBuilderWithFusion:
    def test_fusion_layer_without_prior_base_fails(self, fusion_layer):
        config = BuildConfig(
            project_name="Fail",
            timeline_name="Fail",
            export_path=r"C:\out.mp4",
            layers=[fusion_layer],
            save_project=False,
        )
        pm = MagicMock()

        with (
            patch("dvre.core.builder.builder.ProjectService"),
            patch("dvre.core.builder.builder.MediaService"),
            patch("dvre.core.builder.builder.TimelineService") as mock_ts,
            patch("dvre.core.builder.builder.FusionService"),
        ):
            mock_ts_instance = mock_ts.return_value
            mock_ts_instance.get_compound_info.side_effect = ResolveError(
                "FusionLayer has no previous compound"
            )

            with pytest.raises(ResolveError):
                OutputBuilder(pm).build(config)

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from dvre.editing.context import BuildContext, ContextFactory
from dvre.editing.fusion import FusionService
from dvre.editing.media import MediaService
from dvre.editing.project import ProjectService
from dvre.editing.timeline import TimelineService
from dvre.schemas.api import TimelineSettings
from dvre.utils.errors import ResolveError


class _FakeValidator:
    def __init__(self):
        self.called_with = None

    def assert_meta(self, path: str) -> None:
        self.called_with = path


@pytest.fixture
def project_manager() -> MagicMock:
    return MagicMock()


class TestBuildContext:
    def test_project_unset(self):
        context = BuildContext(project_manager=MagicMock())
        with pytest.raises(ResolveError):
            context.project

    def test_media_pool_unset(self):
        context = BuildContext(project_manager=MagicMock())
        with pytest.raises(ResolveError):
            context.media_pool

    def test_timeline_unset(self):
        context = BuildContext(project_manager=MagicMock())
        with pytest.raises(ResolveError):
            context.timeline

    def test_project_and_timeline_set(self):
        context = BuildContext(project_manager=MagicMock())
        context._project = MagicMock()
        context._timeline = MagicMock()
        assert context.project is context._project
        assert context.timeline is context._timeline


class TestContextFactory:
    def test_create_project_success(self, project_manager):
        project = MagicMock()
        project_manager.CreateProject.return_value = project

        context = ContextFactory(project_manager).create(
            "Test", "Timeline", TimelineSettings()
        )

        project_manager.CreateProject.assert_called_once_with("Test", None)
        project.SetSetting.assert_any_call("timelineResolutionWidth", str(1920))
        project.SetSetting.assert_any_call("timelineResolutionHeight", str(1080))
        project.SetSetting.assert_any_call("timelineFrameRate", "60")
        assert context.project is project
        assert context.media_pool is project.GetMediaPool.return_value

    def test_create_project_super_scale(self, project_manager):
        project = MagicMock()
        project.SetSetting.return_value = True
        project_manager.CreateProject.return_value = project

        ContextFactory(project_manager).create(
            "Test", "Timeline", TimelineSettings(super_scale=2)
        )

        project.SetSetting.assert_any_call("superScale", 2)

    def test_create_project_failure(self, project_manager):
        project_manager.CreateProject.return_value = None

        with pytest.raises(ResolveError):
            ContextFactory(project_manager).create(
                "Test", "Timeline", TimelineSettings()
            )

    def test_create_project_super_scale_failure(self, project_manager):
        project = MagicMock()
        project.SetSetting.return_value = False
        project_manager.CreateProject.return_value = project

        with pytest.raises(ResolveError):
            ContextFactory(project_manager).create(
                "Test", "Timeline", TimelineSettings(super_scale=4)
            )

    def test_create_timeline_success(self, project_manager):
        project = MagicMock()
        timeline = MagicMock()
        project_manager.CreateProject.return_value = project
        project.GetMediaPool.return_value.CreateEmptyTimeline.return_value = timeline
        project.SetCurrentTimeline.return_value = True

        context = ContextFactory(project_manager).create(
            "Test", "Timeline", TimelineSettings()
        )

        assert context.timeline is timeline
        project.SetCurrentTimeline.assert_called_once_with(timeline)

    def test_create_timeline_failure(self, project_manager):
        project = MagicMock()
        project_manager.CreateProject.return_value = project
        project.GetMediaPool.return_value.CreateEmptyTimeline.return_value = None

        with pytest.raises(ResolveError):
            ContextFactory(project_manager).create(
                "Test", "Timeline", TimelineSettings()
            )

    def test_set_current_timeline_failure(self, project_manager):
        project = MagicMock()
        timeline = MagicMock()
        project_manager.CreateProject.return_value = project
        project.GetMediaPool.return_value.CreateEmptyTimeline.return_value = timeline
        project.SetCurrentTimeline.return_value = False

        with pytest.raises(ResolveError):
            ContextFactory(project_manager).create(
                "Test", "Timeline", TimelineSettings()
            )


class TestMediaService:
    def test_import_media_success(self):
        media_pool = MagicMock()
        item = MagicMock()
        media_pool.ImportMedia.return_value = [item]
        context = BuildContext(project_manager=MagicMock())
        context._media_pool = media_pool
        validator = _FakeValidator()

        result = MediaService(context).import_media("C:/clip.mp4", validator)

        assert validator.called_with == "C:/clip.mp4"
        media_pool.ImportMedia.assert_called_once_with(["C:/clip.mp4"])
        assert result is item

    def test_import_media_failure(self):
        media_pool = MagicMock()
        media_pool.ImportMedia.return_value = None
        context = BuildContext(project_manager=MagicMock())
        context._media_pool = media_pool

        with pytest.raises(ResolveError):
            MediaService(context).import_media("C:/clip.mp4", _FakeValidator())


class TestProjectService:
    def test_save_project_success(self):
        pm = MagicMock()
        pm.SaveProject.return_value = True
        context = BuildContext(project_manager=pm)
        context._project = MagicMock()

        ProjectService(context).save_current_project()

        pm.SaveProject.assert_called_once_with()

    def test_save_project_failure(self):
        pm = MagicMock()
        pm.SaveProject.return_value = False
        context = BuildContext(project_manager=pm)

        with pytest.raises(ResolveError):
            ProjectService(context).save_current_project()

    def test_export_project(self):
        project = MagicMock()
        project.AddRenderJob.return_value = "task_42"
        context = BuildContext(project_manager=MagicMock())
        context._project = project

        task_id = ProjectService(context).export_project(
            "C:/out", "video", 1920, 1080, 25.0
        )

        project.SetCurrentRenderFormatAndCodec.assert_called_once_with("MP4", "H264")
        project.SetRenderSettings.assert_called_once()
        project.StartRendering.assert_called_once_with(
            ["task_42"], isInteractiveMode=False
        )
        assert task_id == "task_42"

    def test_get_render_task_status(self):
        project = MagicMock()
        project.GetRenderJobStatus.return_value = {"JobStatus": "Complete"}
        context = BuildContext(project_manager=MagicMock())
        context._project = project

        status = ProjectService(context).get_render_task_status("task_42")

        project.GetRenderJobStatus.assert_called_once_with("task_42")
        assert status == {"JobStatus": "Complete"}


class TestTimelineService:
    def _context(self) -> BuildContext:
        timeline = MagicMock()
        timeline.GetStartFrame.return_value = 1000
        media_pool = MagicMock()
        context = BuildContext(project_manager=MagicMock())
        context._timeline = timeline
        context._media_pool = media_pool
        return context

    def test_ensure_track_count_adds_tracks(self):
        context = self._context()
        context.timeline.GetTrackCount.return_value = 2
        context.timeline.AddTrack.return_value = True

        TimelineService(context).ensure_track_count("video", 4)

        assert context.timeline.AddTrack.call_count == 2
        context.timeline.AddTrack.assert_called_with("video", None)

    def test_ensure_track_count_audio_stereo(self):
        context = self._context()
        context.timeline.GetTrackCount.return_value = 1
        context.timeline.AddTrack.return_value = True

        TimelineService(context).ensure_track_count("audio", 3)

        context.timeline.AddTrack.assert_called_with("audio", "stereo")

    def test_ensure_track_count_noop_when_enough(self):
        context = self._context()
        context.timeline.GetTrackCount.return_value = 4

        TimelineService(context).ensure_track_count("video", 3)

        context.timeline.AddTrack.assert_not_called()

    def test_ensure_track_count_failure(self):
        context = self._context()
        context.timeline.GetTrackCount.return_value = 1
        context.timeline.AddTrack.return_value = False

        with pytest.raises(ResolveError):
            TimelineService(context).ensure_track_count("video", 3)

    def test_place_clip_success(self):
        context = self._context()
        item = MagicMock()
        context.media_pool.AppendToTimeline.return_value = [item]
        media_item = MagicMock()

        result = TimelineService(context).place_clip(media_item, 2, 10, 50, 5, 1)

        clip_info = context.media_pool.AppendToTimeline.call_args.args[0][0]
        assert clip_info["mediaPoolItem"] is media_item
        assert clip_info["startFrame"] == 10
        assert clip_info["endFrame"] == 50
        assert clip_info["trackIndex"] == 2
        assert clip_info["recordFrame"] == 1005
        assert clip_info["mediaType"] == 1
        assert result is item

    def test_place_clip_failure(self):
        context = self._context()
        context.media_pool.AppendToTimeline.return_value = None

        with pytest.raises(ResolveError):
            TimelineService(context).place_clip(MagicMock(), 1, 0, 100, 0, 1)

    def test_compound_clip_direct(self):
        context = self._context()
        context.timeline.GetTrackCount.return_value = 1
        context.timeline.GetItemListInTrack.return_value = [MagicMock()]
        compound = MagicMock()
        context.timeline.CreateCompoundClip.return_value = compound

        result = TimelineService(context).compound_clip({"name": "Layer1"})

        assert result is compound
        context.timeline.CreateCompoundClip.assert_called_once()

    def test_compound_clip_fallback_search(self):
        context = self._context()
        context.timeline.GetTrackCount.return_value = 1
        context.timeline.GetItemListInTrack.return_value = [MagicMock()]
        context.timeline.CreateCompoundClip.return_value = None
        found = MagicMock()
        found.GetName.return_value = "Layer1"
        context.timeline.GetItemListInTrack.return_value = [found]

        result = TimelineService(context).compound_clip({"name": "Layer1"})

        assert result is found

    def test_compound_clip_fallback_not_found(self):
        context = self._context()
        context.timeline.GetTrackCount.return_value = 1
        context.timeline.GetItemListInTrack.return_value = [MagicMock()]
        context.timeline.CreateCompoundClip.return_value = None
        other = MagicMock()
        other.GetName.return_value = "Other"
        context.timeline.GetItemListInTrack.return_value = [other]

        with pytest.raises(ResolveError):
            TimelineService(context).compound_clip({"name": "Layer1"})

    def test_delete_clips_success(self):
        context = self._context()
        context.timeline.DeleteClips.return_value = True
        items = [MagicMock()]

        result = TimelineService(context).delete_clips(items)

        context.timeline.DeleteClips.assert_called_once_with(items, False)
        assert result is True

    def test_delete_clips_failure(self):
        context = self._context()
        context.timeline.DeleteClips.return_value = False

        with pytest.raises(ResolveError):
            TimelineService(context).delete_clips([MagicMock()])

    def test_get_compound_info(self):
        context = self._context()
        item = MagicMock()
        item.GetMediaPoolItem.return_value = "mpi"
        item.GetStart.return_value = 1200
        item.GetEnd.return_value = 1500

        mpi, start, end = TimelineService(context).get_compound_info(item)

        assert (mpi, start, end) == ("mpi", 200, 500)

    def test_start_frame(self):
        context = self._context()
        assert TimelineService(context).start_frame == 1000


class TestFusionService:
    def _context(self) -> BuildContext:
        context = BuildContext(project_manager=MagicMock())
        context._timeline = MagicMock()
        return context

    def test_create_fusion_segment_without_comp(self):
        context = self._context()
        clip = MagicMock()
        context.timeline.CreateFusionClip.return_value = clip
        segment = MagicMock()
        segment.start_frame = 0
        segment.end_frame = 100
        segment.composition = None

        result = FusionService(context).create_fusion_segment(segment, [])

        context.timeline.CreateFusionClip.assert_called_once_with([])
        assert result is clip

    def test_create_fusion_segment_with_comp(self):
        context = self._context()
        clip = MagicMock()
        clip.ImportFusionComp.return_value = MagicMock()
        context.timeline.CreateFusionClip.return_value = clip
        segment = MagicMock()
        segment.start_frame = 0
        segment.end_frame = 100
        segment.composition = "Composition { }"

        with patch("dvre.editing.fusion.NamedTemporaryFile") as mock_temp:
            mock_file = MagicMock()
            mock_file.name = "C:/tmp/comp.comp"
            mock_temp.return_value = mock_file

            FusionService(context).create_fusion_segment(segment, [])

            mock_file.write.assert_called_once_with("Composition { }")
            clip.ImportFusionComp.assert_called_once_with("C:/tmp/comp.comp")

    def test_create_fusion_segment_failure(self):
        context = self._context()
        context.timeline.CreateFusionClip.return_value = None
        segment = MagicMock()
        segment.start_frame = 0
        segment.end_frame = 100

        with pytest.raises(ResolveError):
            FusionService(context).create_fusion_segment(segment, [])

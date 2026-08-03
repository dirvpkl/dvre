from __future__ import annotations

from unittest.mock import patch

import pytest

from dvre.utils.media import AudioValidator, VideoValidator


class TestVideoValidator:
    def test_valid_video(self):
        with patch("dvre.utils.media._get_video_meta") as mock_meta:
            mock_meta.return_value = {"width": 1920, "height": 1080, "fps": 25.0}
            VideoValidator(1920, 1080, 25.0).assert_meta("C:/clip.mp4")
        mock_meta.assert_called_once_with("C:/clip.mp4")

    def test_fps_tolerance(self):
        with patch("dvre.utils.media._get_video_meta") as mock_meta:
            mock_meta.return_value = {"width": 1920, "height": 1080, "fps": 25.004}
            VideoValidator(1920, 1080, 25.0).assert_meta("C:/clip.mp4")

    def test_width_mismatch(self):
        with patch("dvre.utils.media._get_video_meta") as mock_meta:
            mock_meta.return_value = {"width": 1280, "height": 1080, "fps": 25.0}
            with pytest.raises(ValueError):
                VideoValidator(1920, 1080, 25.0).assert_meta("C:/clip.mp4")

    def test_height_mismatch(self):
        with patch("dvre.utils.media._get_video_meta") as mock_meta:
            mock_meta.return_value = {"width": 1920, "height": 720, "fps": 25.0}
            with pytest.raises(ValueError):
                VideoValidator(1920, 1080, 25.0).assert_meta("C:/clip.mp4")

    def test_fps_mismatch(self):
        with patch("dvre.utils.media._get_video_meta") as mock_meta:
            mock_meta.return_value = {"width": 1920, "height": 1080, "fps": 30.0}
            with pytest.raises(ValueError):
                VideoValidator(1920, 1080, 25.0).assert_meta("C:/clip.mp4")


class TestAudioValidator:
    def test_wav_accepted(self):
        AudioValidator.assert_meta("C:/audio.wav")

    @pytest.mark.parametrize("path", ["C:/audio.mp3", "C:/audio.wavx", "C:/audio"])
    def test_non_wav_rejected(self, path):
        with pytest.raises(ValueError):
            AudioValidator.assert_meta(path)

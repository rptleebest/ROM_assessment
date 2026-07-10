"""MediaPipe PoseLandmarker wrapper for Streamlit/WebRTC.

This version avoids importing OpenCV (`cv2`) so the app can run on
Streamlit Cloud and on computers without Python/VS Code installation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, List
import time
import threading

import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class PoseEstimator:
    """Small wrapper around MediaPipe Tasks PoseLandmarker."""

    def __init__(self, model_path: str | Path = "pose_landmarker_full.task", num_poses: int = 1) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Pose model file not found: {self.model_path}. "
                "Put pose_landmarker_full.task in the app directory."
            )
        model_bytes = self.model_path.read_bytes()
        base_options = python.BaseOptions(model_asset_buffer=model_bytes)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=num_poses,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._lock = threading.Lock()
        self._landmarker = vision.PoseLandmarker.create_from_options(options)
        self._last_ts = 0

    def detect_rgb(self, rgb_frame: np.ndarray) -> List[Any]:
        """Return one pose landmark list, or an empty list when no pose is detected."""
        if rgb_frame.dtype != np.uint8:
            rgb_frame = rgb_frame.astype(np.uint8)
        rgb = np.ascontiguousarray(rgb_frame)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = int(time.time() * 1000)
        if ts <= self._last_ts:
            ts = self._last_ts + 1
        self._last_ts = ts
        with self._lock:
            result = self._landmarker.detect_for_video(image, ts)
        if result.pose_landmarks:
            return result.pose_landmarks[0]
        return []

    def close(self) -> None:
        with self._lock:
            if self._landmarker is not None:
                self._landmarker.close()
                self._landmarker = None

"""
Minimal cv2 compatibility stub for Streamlit Cloud + MediaPipe Tasks.

Why this exists:
- The Python mediapipe package imports `cv2` internally for drawing helpers.
- This app does not use OpenCV drawing or GUI APIs; rendering is done with PIL.
- On some Streamlit Cloud Linux images, importing the real OpenCV binary can fail
  because GUI/shared-library dependencies are unavailable.
- Placing this module in the app directory makes `import cv2` resolve here first,
  allowing MediaPipe Tasks to import without loading the OpenCV binary.

This is NOT a full OpenCV implementation. Do not use cv2.imshow, VideoCapture,
or OpenCV image processing in this Cloud-safe app.
"""
from __future__ import annotations

import numpy as np

# Common constants referenced by MediaPipe drawing utilities.
LINE_AA = 16
LINE_8 = 8
FILLED = -1
FONT_HERSHEY_SIMPLEX = 0
FONT_HERSHEY_PLAIN = 1
FONT_HERSHEY_DUPLEX = 2
FONT_HERSHEY_COMPLEX = 3
FONT_HERSHEY_TRIPLEX = 4
FONT_HERSHEY_COMPLEX_SMALL = 5
FONT_HERSHEY_SCRIPT_SIMPLEX = 6
FONT_HERSHEY_SCRIPT_COMPLEX = 7

COLOR_RGB2BGR = 4
COLOR_BGR2RGB = 4
COLOR_RGB2GRAY = 7
COLOR_BGR2GRAY = 6
COLOR_GRAY2RGB = 8
COLOR_GRAY2BGR = 8

IMREAD_COLOR = 1
IMREAD_UNCHANGED = -1
INTER_LINEAR = 1
INTER_AREA = 3

CV_8UC1 = 0
CV_8UC3 = 16


def _as_array(img):
    return np.asarray(img)


def cvtColor(img, code):
    arr = _as_array(img)
    if code in (COLOR_RGB2BGR, COLOR_BGR2RGB):
        if arr.ndim == 3 and arr.shape[-1] >= 3:
            out = arr.copy()
            out[..., :3] = out[..., :3][..., ::-1]
            return out
        return arr
    if code in (COLOR_RGB2GRAY, COLOR_BGR2GRAY):
        if arr.ndim == 3:
            return np.mean(arr[..., :3], axis=-1).astype(arr.dtype)
        return arr
    if code in (COLOR_GRAY2RGB, COLOR_GRAY2BGR):
        if arr.ndim == 2:
            return np.stack([arr, arr, arr], axis=-1)
        return arr
    return arr


def flip(img, flipCode):
    arr = _as_array(img)
    if flipCode == 0:
        return np.flip(arr, axis=0)
    if flipCode == 1:
        return np.flip(arr, axis=1)
    if flipCode == -1:
        return np.flip(np.flip(arr, axis=0), axis=1)
    return arr


def resize(img, dsize, interpolation=INTER_LINEAR):
    # Lightweight nearest-neighbor fallback. The app should use PIL for resizing.
    arr = _as_array(img)
    width, height = dsize
    if arr.size == 0 or width <= 0 or height <= 0:
        return arr
    y_idx = (np.linspace(0, arr.shape[0] - 1, height)).astype(int)
    x_idx = (np.linspace(0, arr.shape[1] - 1, width)).astype(int)
    return arr[np.ix_(y_idx, x_idx)]


def imdecode(buf, flags=IMREAD_COLOR):
    raise NotImplementedError("cv2.imdecode is not available in this Cloud-safe stub.")


def imencode(ext, img):
    raise NotImplementedError("cv2.imencode is not available in this Cloud-safe stub.")


def getTextSize(text, fontFace, fontScale, thickness):
    return ((int(len(str(text)) * 10 * float(fontScale)), int(20 * float(fontScale))), 0)


def circle(img, center, radius, color, thickness=1, lineType=LINE_AA):
    return img


def line(img, pt1, pt2, color, thickness=1, lineType=LINE_AA):
    return img


def rectangle(img, pt1, pt2, color, thickness=1, lineType=LINE_AA):
    return img


def putText(img, text, org, fontFace, fontScale, color, thickness=1, lineType=LINE_AA):
    return img


def polylines(img, pts, isClosed, color, thickness=1, lineType=LINE_AA):
    return img


def fillPoly(img, pts, color, lineType=LINE_AA):
    return img


def addWeighted(src1, alpha, src2, beta, gamma):
    return (np.asarray(src1) * alpha + np.asarray(src2) * beta + gamma).astype(np.asarray(src1).dtype)


def convexHull(points):
    return np.asarray(points)


def __getattr__(name):
    # Make unexpected drawing-only attributes less likely to crash imports.
    if name.startswith("COLOR_") or name.startswith("FONT_") or name.startswith("LINE_"):
        return 0
    raise AttributeError(f"cv2 stub does not implement attribute: {name}")

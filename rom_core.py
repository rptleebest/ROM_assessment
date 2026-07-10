"""
ROM Streamlit app core logic.

This module is intentionally independent from Streamlit and WebRTC so it can be
unit-tested and reused in a desktop app. Measurements are intended for
education/feedback, not diagnostic use.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import math
import statistics
import json

import numpy as np

Point = Tuple[float, float]

LANDMARK_ID: Dict[str, int] = {
    "nose": 0,
    "left_eye": 2,
    "right_eye": 5,
    "left_ear": 7,
    "right_ear": 8,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_pinky": 17,
    "right_pinky": 18,
    "left_index": 19,
    "right_index": 20,
    "left_thumb": 21,
    "right_thumb": 22,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_heel": 29,
    "right_heel": 30,
    "left_foot_index": 31,
    "right_foot_index": 32,
}


@dataclass(frozen=True)
class MeasurementSpec:
    category: str
    joint: str
    label: str
    motion_id: str
    calc_type: str
    guide: str
    target_sign: int = 1
    delta_sign: int = 1
    side_required: bool = False
    side_default: str = "right"
    points: Tuple[str, str, str] = ("", "", "")
    reliability: str = "교육/피드백용"
    unsupported: bool = False
    clinical_note: str = ""

    def display_name(self) -> str:
        return f"{self.category} / {self.joint} / {self.label}"


# calc_type
# - neck_flex_ext: shoulder midpoint to ear midpoint, signed from vertical.
# - neck_lateral: shoulder midpoint to nose, signed from vertical.
# - neck_rotation_proxy: nose offset from ear midpoint, not true CROM.
# - trunk: hip midpoint to shoulder midpoint, signed from vertical.
# - three_point_unsigned: absolute angle. ROM direction is raw-neutral times delta_sign.
# - signed_joint: signed angle from proximal-center to distal-center. ROM direction is raw-neutral times target_sign.

CATALOG: Dict[str, Dict[str, List[MeasurementSpec]]] = {
    "척추": {
        "목": [
            MeasurementSpec(
                "척추", "목", "굴곡 - 측면 촬영", "neck_flexion", "neck_flex_ext",
                "환자의 옆면이 카메라를 향하게 합니다. 기준선이 안정되면 목을 굴곡한 뒤 처음 위치로 돌아옵니다. 방향이 반대로 판정되면 화면의 '방향 반전'을 켜세요.",
                target_sign=1,
                reliability="보통: 측면 촬영에서 중립 대비 변화량",
            ),
            MeasurementSpec(
                "척추", "목", "신전 - 측면 촬영", "neck_extension", "neck_flex_ext",
                "환자의 옆면이 카메라를 향하게 합니다. 기준선이 안정되면 목을 신전한 뒤 처음 위치로 돌아옵니다. 방향이 반대로 판정되면 '방향 반전'을 켜세요.",
                target_sign=-1,
                reliability="보통: 측면 촬영에서 중립 대비 변화량",
            ),
            MeasurementSpec(
                "척추", "목", "좌측 굴곡 - 정면 촬영", "neck_left_lateral", "neck_lateral",
                "환자가 카메라를 정면으로 바라보게 합니다. 목을 좌측으로 기울인 뒤 처음 위치로 돌아옵니다. 좌우가 반대로 나오면 '방향 반전'을 켜세요.",
                target_sign=-1,
                reliability="좋음: 정면 촬영에서 피드백용으로 적합",
            ),
            MeasurementSpec(
                "척추", "목", "우측 굴곡 - 정면 촬영", "neck_right_lateral", "neck_lateral",
                "환자가 카메라를 정면으로 바라보게 합니다. 목을 우측으로 기울인 뒤 처음 위치로 돌아옵니다. 좌우가 반대로 나오면 '방향 반전'을 켜세요.",
                target_sign=1,
                reliability="좋음: 정면 촬영에서 피드백용으로 적합",
            ),
            MeasurementSpec(
                "척추", "목", "좌측 회전 - 정면 촬영, 참고값", "neck_left_rotation", "neck_rotation_proxy",
                "코와 양쪽 귀의 상대 위치로 회전 방향을 추정하는 참고값입니다. 실제 임상 CROM 각도가 아닙니다.",
                target_sign=-1,
                reliability="참고값: 실제 회전각 아님",
                clinical_note="목 회전은 단일 웹캠으로 실제 CROM 각도를 정확히 산출하기 어렵습니다.",
            ),
            MeasurementSpec(
                "척추", "목", "우측 회전 - 정면 촬영, 참고값", "neck_right_rotation", "neck_rotation_proxy",
                "코와 양쪽 귀의 상대 위치로 회전 방향을 추정하는 참고값입니다. 실제 임상 CROM 각도가 아닙니다.",
                target_sign=1,
                reliability="참고값: 실제 회전각 아님",
                clinical_note="목 회전은 단일 웹캠으로 실제 CROM 각도를 정확히 산출하기 어렵습니다.",
            ),
        ],
        "가슴/허리(몸통 통합)": [
            MeasurementSpec(
                "척추", "가슴/허리(몸통 통합)", "굴곡 - 측면 촬영", "trunk_flexion", "trunk",
                "측면 촬영에서 어깨 중심과 골반 중심의 기울기 변화를 봅니다. 흉추와 요추를 분리한 값은 아닙니다.",
                target_sign=1,
                reliability="보통: 몸통 통합 참고값",
            ),
            MeasurementSpec(
                "척추", "가슴/허리(몸통 통합)", "신전 - 측면 촬영", "trunk_extension", "trunk",
                "측면 촬영에서 어깨 중심과 골반 중심의 기울기 변화를 봅니다. 흉추와 요추를 분리한 값은 아닙니다.",
                target_sign=-1,
                reliability="보통: 몸통 통합 참고값",
            ),
            MeasurementSpec(
                "척추", "가슴/허리(몸통 통합)", "좌측 굴곡 - 정면 촬영", "trunk_left_lateral", "trunk",
                "정면 촬영에서 몸통을 좌측으로 기울입니다. 흉추/요추 분리 측정은 아닙니다.",
                target_sign=-1,
                reliability="보통: 몸통 통합 참고값",
            ),
            MeasurementSpec(
                "척추", "가슴/허리(몸통 통합)", "우측 굴곡 - 정면 촬영", "trunk_right_lateral", "trunk",
                "정면 촬영에서 몸통을 우측으로 기울입니다. 흉추/요추 분리 측정은 아닙니다.",
                target_sign=1,
                reliability="보통: 몸통 통합 참고값",
            ),
        ],
    },
    "팔": {
        "어깨": [
            MeasurementSpec("팔", "어깨", "굴곡 - 측면 촬영", "shoulder_flexion", "signed_joint", "측정할 쪽의 고관절-어깨-팔꿈치가 잘 보이도록 측면에서 촬영합니다.", target_sign=1, side_required=True, points=("hip", "shoulder", "elbow"), reliability="보통: 촬영 평면 의존"),
            MeasurementSpec("팔", "어깨", "신전 - 측면 촬영", "shoulder_extension", "signed_joint", "측정할 쪽의 고관절-어깨-팔꿈치가 잘 보이도록 측면에서 촬영합니다.", target_sign=-1, side_required=True, points=("hip", "shoulder", "elbow"), reliability="보통: 촬영 평면 의존"),
            MeasurementSpec("팔", "어깨", "벌림 - 정면 촬영", "shoulder_abduction", "signed_joint", "환자가 정면을 보게 하고 어깨-팔꿈치가 잘 보이도록 촬영합니다.", target_sign=1, side_required=True, points=("hip", "shoulder", "elbow"), reliability="보통: 촬영 평면 의존"),
            MeasurementSpec("팔", "어깨", "모음 - 정면 촬영", "shoulder_adduction", "signed_joint", "환자가 정면을 보게 하고 어깨-팔꿈치가 잘 보이도록 촬영합니다.", target_sign=-1, side_required=True, points=("hip", "shoulder", "elbow"), reliability="보통: 촬영 평면 의존"),
        ],
        "팔꿈치": [
            MeasurementSpec("팔", "팔꿈치", "굴곡", "elbow_flexion", "three_point_unsigned", "어깨-팔꿈치-손목이 모두 보이게 촬영합니다. 굽힌 뒤 처음 위치로 돌아옵니다.", delta_sign=-1, side_required=True, points=("shoulder", "elbow", "wrist"), reliability="좋음"),
            MeasurementSpec("팔", "팔꿈치", "신전", "elbow_extension", "three_point_unsigned", "어깨-팔꿈치-손목이 모두 보이게 촬영합니다. 펴는 움직임을 측정합니다.", delta_sign=1, side_required=True, points=("shoulder", "elbow", "wrist"), reliability="좋음"),
        ],
        "손목": [
            MeasurementSpec("팔", "손목", "굴곡/폄 또는 편위 - 참고값", "wrist_reference", "signed_joint", "팔꿈치-손목-검지 landmark를 이용한 참고값입니다. 손목은 Pose만으로 오차가 큽니다.", target_sign=1, side_required=True, points=("elbow", "wrist", "index"), reliability="낮음~보통: 참고값"),
        ],
        "손가락": [
            MeasurementSpec("팔", "손가락", "현재 버전 미지원 - MediaPipe Hands 필요", "finger_unsupported", "unsupported", "손가락 개별 관절은 MediaPipe Hands 추가가 필요합니다.", unsupported=True, reliability="미지원"),
        ],
    },
    "다리": {
        "엉덩이": [
            MeasurementSpec("다리", "엉덩이", "굴곡 - 측면 촬영", "hip_flexion", "signed_joint", "측정할 쪽의 어깨-고관절-무릎이 잘 보이도록 측면에서 촬영합니다. 몸통 보상 움직임을 줄이세요.", target_sign=1, side_required=True, points=("shoulder", "hip", "knee"), reliability="보통"),
            MeasurementSpec("다리", "엉덩이", "신전 - 측면 촬영", "hip_extension", "signed_joint", "측정할 쪽의 어깨-고관절-무릎이 잘 보이도록 측면에서 촬영합니다. 몸통 보상 움직임을 줄이세요.", target_sign=-1, side_required=True, points=("shoulder", "hip", "knee"), reliability="보통"),
            MeasurementSpec("다리", "엉덩이", "벌림 - 정면 촬영", "hip_abduction", "signed_joint", "정면 촬영에서 고관절-무릎이 잘 보이도록 합니다. 골반 보상 움직임을 줄이세요.", target_sign=1, side_required=True, points=("shoulder", "hip", "knee"), reliability="보통"),
            MeasurementSpec("다리", "엉덩이", "모음 - 정면 촬영", "hip_adduction", "signed_joint", "정면 촬영에서 고관절-무릎이 잘 보이도록 합니다. 골반 보상 움직임을 줄이세요.", target_sign=-1, side_required=True, points=("shoulder", "hip", "knee"), reliability="보통"),
        ],
        "무릎": [
            MeasurementSpec("다리", "무릎", "굴곡", "knee_flexion", "three_point_unsigned", "고관절-무릎-발목이 모두 보이게 촬영합니다. 굽힌 뒤 처음 위치로 돌아옵니다.", delta_sign=-1, side_required=True, points=("hip", "knee", "ankle"), reliability="좋음"),
            MeasurementSpec("다리", "무릎", "신전", "knee_extension", "three_point_unsigned", "고관절-무릎-발목이 모두 보이게 촬영합니다. 펴는 움직임을 측정합니다.", delta_sign=1, side_required=True, points=("hip", "knee", "ankle"), reliability="좋음"),
        ],
        "발목": [
            MeasurementSpec("다리", "발목", "배굴 - 측면 촬영", "ankle_dorsiflexion", "three_point_unsigned", "무릎-발목-발끝 landmark가 잘 보이도록 측면에서 촬영합니다.", delta_sign=1, side_required=True, points=("knee", "ankle", "foot_index"), reliability="보통: 발끝 landmark 영향"),
            MeasurementSpec("다리", "발목", "저굴 - 측면 촬영", "ankle_plantarflexion", "three_point_unsigned", "무릎-발목-발끝 landmark가 잘 보이도록 측면에서 촬영합니다.", delta_sign=-1, side_required=True, points=("knee", "ankle", "foot_index"), reliability="보통: 발끝 landmark 영향"),
        ],
        "발가락": [
            MeasurementSpec("다리", "발가락", "현재 버전 미지원 - 일반 Pose만으로 제한", "toe_unsupported", "unsupported", "발가락 개별 관절은 일반 Pose만으로 정확히 측정하기 어렵습니다.", unsupported=True, reliability="미지원"),
        ],
    },
}


def categories() -> List[str]:
    return list(CATALOG.keys())


def joints(category: str) -> List[str]:
    return list(CATALOG[category].keys())


def motions(category: str, joint: str) -> List[MeasurementSpec]:
    return CATALOG[category][joint]


def get_spec_by_id(motion_id: str) -> MeasurementSpec:
    for cat in CATALOG.values():
        for specs in cat.values():
            for spec in specs:
                if spec.motion_id == motion_id:
                    return spec
    raise KeyError(f"Unknown motion_id: {motion_id}")


def lm_visible(landmarks: List[Any], idx: int, threshold: float = 0.45) -> bool:
    if idx < 0 or idx >= len(landmarks):
        return False
    return getattr(landmarks[idx], "visibility", 1.0) >= threshold


def xy(landmarks: List[Any], idx: int, width: int, height: int) -> Point:
    lm = landmarks[idx]
    return (lm.x * width, lm.y * height)


def midpoint(points: List[Point]) -> Optional[Point]:
    if not points:
        return None
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def midpoint_if_visible(landmarks: List[Any], ids: Tuple[str, str], width: int, height: int, thr: float = 0.45) -> Optional[Point]:
    pts: List[Point] = []
    for name in ids:
        idx = LANDMARK_ID[name]
        if lm_visible(landmarks, idx, thr):
            pts.append(xy(landmarks, idx, width, height))
    return midpoint(pts)


def angle_from_vertical(base: Point, top: Point) -> float:
    dx = top[0] - base[0]
    dy_up = base[1] - top[1]
    return math.degrees(math.atan2(dx, dy_up))


def angle3(a: Point, b: Point, c: Point) -> Optional[float]:
    a_np = np.array(a, dtype=float)
    b_np = np.array(b, dtype=float)
    c_np = np.array(c, dtype=float)
    ba = a_np - b_np
    bc = c_np - b_np
    na = np.linalg.norm(ba)
    nc = np.linalg.norm(bc)
    if na == 0 or nc == 0:
        return None
    cosv = float(np.dot(ba, bc) / (na * nc))
    cosv = max(-1.0, min(1.0, cosv))
    return math.degrees(math.acos(cosv))


def signed_joint_angle(proximal: Point, center: Point, distal: Point) -> float:
    """Signed 2D angle from proximal-center vector to distal-center vector."""
    v1 = np.array([proximal[0] - center[0], proximal[1] - center[1]], dtype=float)
    v2 = np.array([distal[0] - center[0], distal[1] - center[1]], dtype=float)
    a1 = math.atan2(v1[1], v1[0])
    a2 = math.atan2(v2[1], v2[0])
    deg = math.degrees(a2 - a1)
    while deg > 180:
        deg -= 360
    while deg < -180:
        deg += 360
    return deg


def resolve_side_part(side: str, part: str) -> str:
    return f"{side}_{part}"


@dataclass
class MeasurementResult:
    valid: bool
    raw_angle: Optional[float] = None
    points: List[Point] = field(default_factory=list)
    lines: List[Tuple[Point, Point]] = field(default_factory=list)
    message: str = ""
    clinical_note: str = ""


def compute_measurement(spec: MeasurementSpec, side: str, landmarks: List[Any], width: int, height: int, visibility_threshold: float = 0.45) -> MeasurementResult:
    if spec.unsupported or spec.calc_type == "unsupported":
        return MeasurementResult(False, message="현재 버전에서는 지원하지 않는 측정입니다.")

    try:
        if spec.calc_type == "neck_flex_ext":
            shoulder_mid = midpoint_if_visible(landmarks, ("left_shoulder", "right_shoulder"), width, height, visibility_threshold)
            ear_mid = midpoint_if_visible(landmarks, ("left_ear", "right_ear"), width, height, visibility_threshold)
            if ear_mid is None and lm_visible(landmarks, LANDMARK_ID["nose"], visibility_threshold):
                ear_mid = xy(landmarks, LANDMARK_ID["nose"], width, height)
            if shoulder_mid is None or ear_mid is None:
                return MeasurementResult(False, message="어깨 또는 귀 landmark가 명확하지 않습니다.")
            raw = angle_from_vertical(shoulder_mid, ear_mid)
            return MeasurementResult(True, raw, [shoulder_mid, ear_mid], [(shoulder_mid, ear_mid)], clinical_note=spec.clinical_note)

        if spec.calc_type == "neck_lateral":
            shoulder_mid = midpoint_if_visible(landmarks, ("left_shoulder", "right_shoulder"), width, height, visibility_threshold)
            if shoulder_mid is None or not lm_visible(landmarks, LANDMARK_ID["nose"], visibility_threshold):
                return MeasurementResult(False, message="어깨 또는 코 landmark가 명확하지 않습니다.")
            nose = xy(landmarks, LANDMARK_ID["nose"], width, height)
            raw = angle_from_vertical(shoulder_mid, nose)
            return MeasurementResult(True, raw, [shoulder_mid, nose], [(shoulder_mid, nose)], clinical_note=spec.clinical_note)

        if spec.calc_type == "neck_rotation_proxy":
            ids = [LANDMARK_ID["nose"], LANDMARK_ID["left_ear"], LANDMARK_ID["right_ear"]]
            if not all(lm_visible(landmarks, i, visibility_threshold) for i in ids):
                return MeasurementResult(False, message="코와 양쪽 귀 landmark가 모두 필요합니다.")
            nose = xy(landmarks, LANDMARK_ID["nose"], width, height)
            left_ear = xy(landmarks, LANDMARK_ID["left_ear"], width, height)
            right_ear = xy(landmarks, LANDMARK_ID["right_ear"], width, height)
            ear_mid = midpoint([left_ear, right_ear])
            assert ear_mid is not None
            ear_width = np.linalg.norm(np.array(left_ear) - np.array(right_ear))
            if ear_width < 10:
                return MeasurementResult(False, message="귀 간 거리가 너무 작아 회전 참고값을 계산할 수 없습니다.")
            raw = math.degrees(math.atan2(nose[0] - ear_mid[0], ear_width))
            return MeasurementResult(True, raw, [nose, left_ear, right_ear, ear_mid], [(left_ear, right_ear), (ear_mid, nose)], clinical_note=spec.clinical_note)

        if spec.calc_type == "trunk":
            shoulder_mid = midpoint_if_visible(landmarks, ("left_shoulder", "right_shoulder"), width, height, visibility_threshold)
            hip_mid = midpoint_if_visible(landmarks, ("left_hip", "right_hip"), width, height, visibility_threshold)
            if shoulder_mid is None or hip_mid is None:
                return MeasurementResult(False, message="어깨 또는 골반 landmark가 명확하지 않습니다.")
            raw = angle_from_vertical(hip_mid, shoulder_mid)
            return MeasurementResult(True, raw, [hip_mid, shoulder_mid], [(hip_mid, shoulder_mid)], clinical_note=spec.clinical_note)

        if spec.calc_type in {"three_point_unsigned", "signed_joint"}:
            pts: List[Point] = []
            for part in spec.points:
                name = resolve_side_part(side, part)
                if name not in LANDMARK_ID:
                    return MeasurementResult(False, message=f"{name} landmark가 없습니다.")
                idx = LANDMARK_ID[name]
                if not lm_visible(landmarks, idx, visibility_threshold):
                    return MeasurementResult(False, message=f"{name} landmark가 명확하지 않습니다.")
                pts.append(xy(landmarks, idx, width, height))
            if spec.calc_type == "three_point_unsigned":
                raw = angle3(pts[0], pts[1], pts[2])
            else:
                raw = signed_joint_angle(pts[0], pts[1], pts[2])
            if raw is None:
                return MeasurementResult(False, message="각도 계산 실패")
            return MeasurementResult(True, raw, pts, [(pts[0], pts[1]), (pts[1], pts[2])], clinical_note=spec.clinical_note)

        return MeasurementResult(False, message=f"알 수 없는 calc_type: {spec.calc_type}")
    except Exception as exc:
        return MeasurementResult(False, message=f"측정 계산 오류: {exc}")


def direction_value(spec: MeasurementSpec, raw_angle: float, neutral_angle: float, reverse_direction: bool = False) -> Tuple[float, float, float]:
    """Return target_value, opposite_value, signed_change.

    target_value is positive only when the movement is in the selected direction.
    opposite_value is positive only when movement is opposite to the selected direction.
    This prevents a wrong-direction movement from being accepted as a valid ROM rep.
    """
    if spec.calc_type == "three_point_unsigned":
        signed_change = spec.delta_sign * (raw_angle - neutral_angle)
    else:
        sign = spec.target_sign * (-1 if reverse_direction else 1)
        signed_change = sign * (raw_angle - neutral_angle)
    target = max(0.0, signed_change)
    opposite = max(0.0, -signed_change)
    return target, opposite, signed_change


@dataclass
class AnalyzerStatus:
    state: str = "WAITING_STABLE"
    voice_id: int = 0
    voice_text: str = ""
    screen_text: str = "중립 자세를 취해 주세요."
    rep_count: int = 0
    peaks: List[float] = field(default_factory=list)
    current_peak: float = 0.0
    target_value: float = 0.0
    opposite_value: float = 0.0
    signed_change: float = 0.0
    neutral_angle: Optional[float] = None
    stable_progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    alignment_ok: bool = False
    invalid_reason: str = ""


class GuidedROMAnalyzer:
    """Strict 3-repetition ROM analyzer.

    Valid rep: stable neutral -> selected-direction movement over threshold -> return to neutral.
    Invalid rep: opposite-direction movement, unclear landmarks, or return with unstable posture.
    """

    def __init__(
        self,
        spec: MeasurementSpec,
        reps: int = 3,
        stable_seconds: float = 2.0,
        start_threshold: float = 8.0,
        return_threshold: float = 3.0,
        opposite_threshold: float = 5.0,
        stability_angle_sd: float = 1.8,
        fps_assumption: float = 20.0,
        reverse_direction: bool = False,
    ) -> None:
        self.spec = spec
        self.reps = reps
        self.stable_seconds = stable_seconds
        self.start_threshold = start_threshold
        self.return_threshold = return_threshold
        self.opposite_threshold = opposite_threshold
        self.stability_angle_sd = stability_angle_sd
        self.fps_assumption = fps_assumption
        self.reverse_direction = reverse_direction
        self.window = deque(maxlen=max(8, int(stable_seconds * fps_assumption)))
        self.status = AnalyzerStatus()
        self._voice_counter = 0
        self._said_stabilizing = False
        self._cooldown_frames = 0
        self._speak("측정을 시작합니다. 중립 자세를 취해 주세요. 기준선이 안정되면 측정을 시작합니다.")

    def _speak(self, text: str) -> None:
        self._voice_counter += 1
        self.status.voice_id = self._voice_counter
        self.status.voice_text = text

    def reset(self, full: bool = True, message: Optional[str] = None) -> None:
        self.window.clear()
        self.status = AnalyzerStatus()
        self._said_stabilizing = False
        self._cooldown_frames = 0
        if not full:
            # Preserve completed peaks after a failed current movement.
            pass
        if message:
            self._speak(message)
        else:
            self._speak("중립 자세를 다시 잡아 주세요. 기준선이 안정되면 측정을 시작합니다.")

    def _alignment_ok(self, raw_angle: float, valid: bool) -> Tuple[bool, float]:
        if not valid:
            self.window.clear()
            return False, 0.0
        self.window.append(raw_angle)
        if len(self.window) < self.window.maxlen:
            return False, len(self.window) / float(self.window.maxlen)
        vals = list(self.window)
        sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        return sd <= self.stability_angle_sd, min(1.0, max(0.0, 1.0 - sd / max(self.stability_angle_sd, 0.1)))

    def update(self, raw_angle: Optional[float], valid: bool) -> AnalyzerStatus:
        if raw_angle is None or not valid:
            self.status.alignment_ok = False
            self.status.screen_text = "landmark가 명확하지 않습니다. 자세, 조명, 거리, 촬영 방향을 조정하세요."
            return self.status

        alignment_ok, progress = self._alignment_ok(raw_angle, valid)
        self.status.alignment_ok = alignment_ok
        self.status.stable_progress = progress
        self.status.state = self.status.state

        if self.status.state == "WAITING_STABLE":
            self.status.screen_text = f"중립 자세 안정 대기 중... {progress*100:.0f}%"
            if progress > 0.45 and not self._said_stabilizing:
                self._said_stabilizing = True
                self._speak("기준선이 안정되고 있습니다. 그대로 유지하세요.")
            if alignment_ok:
                neutral = sum(self.window) / len(self.window)
                self.status.neutral_angle = neutral
                self.status.state = "READY"
                self.status.current_peak = 0.0
                self._cooldown_frames = int(0.8 * self.fps_assumption)
                self._speak("기준선이 안정되었습니다. 이제 측정을 시작합니다. 관절을 움직이세요. 끝 범위까지 움직인 후 처음 위치로 돌아오세요.")
            return self.status

        if self.status.neutral_angle is None:
            self.status.state = "WAITING_STABLE"
            return self.status

        target, opposite, signed_change = direction_value(self.spec, raw_angle, self.status.neutral_angle, self.reverse_direction)
        self.status.target_value = target
        self.status.opposite_value = opposite
        self.status.signed_change = signed_change

        if self._cooldown_frames > 0:
            self._cooldown_frames -= 1

        if self.status.state == "READY":
            self.status.screen_text = f"{self.status.rep_count + 1}회 측정 준비: 선택한 방향으로 움직이세요."
            if opposite >= self.opposite_threshold:
                self._invalidate("선택한 방향과 반대 방향으로 움직였습니다. 이번 움직임은 기록하지 않습니다. 기준선을 다시 맞춰 주세요.")
                return self.status
            if self._cooldown_frames <= 0 and target >= self.start_threshold:
                self.status.state = "MOVING"
                self.status.current_peak = target
                self.status.screen_text = "움직임 측정 중: 끝 범위까지 움직인 후 처음 위치로 돌아오세요."
            return self.status

        if self.status.state == "MOVING":
            self.status.current_peak = max(self.status.current_peak, target)
            self.status.screen_text = f"움직임 측정 중... 현재 {target:.1f}°, 최고 {self.status.current_peak:.1f}°"
            if opposite >= self.opposite_threshold:
                self._invalidate("선택한 방향과 반대 방향으로 움직였습니다. 이번 움직임은 기록하지 않습니다. 기준선을 다시 맞춰 주세요.")
                return self.status
            if target <= self.return_threshold:
                if not alignment_ok:
                    self._invalidate("관절 움직임 위치가 잘못되었습니다. 이번 움직임은 기록하지 않습니다. 기준선을 다시 맞춰 주세요.")
                    return self.status
                peak = float(self.status.current_peak)
                if peak < self.start_threshold:
                    self._invalidate("움직임 범위가 너무 작아 측정하지 않았습니다. 기준 자세를 다시 잡아 주세요.")
                    return self.status
                self.status.peaks.append(peak)
                self.status.rep_count = len(self.status.peaks)
                self.status.current_peak = 0.0
                if self.status.rep_count >= self.reps:
                    self.status.state = "COMPLETE"
                    self.status.result = self._make_result()
                    mean_rom = self.status.result["mean_rom"]
                    self.status.screen_text = "모든 측정이 끝났습니다. 결과를 확인하세요."
                    self._speak(f"모든 측정이 끝났습니다. 결과를 확인하세요. 평균 관절가동범위는 {mean_rom:.1f}도입니다.")
                else:
                    next_rep = self.status.rep_count + 1
                    self.status.state = "READY"
                    self._cooldown_frames = int(1.0 * self.fps_assumption)
                    self._speak(f"정상적으로 측정되었습니다. {self.status.rep_count}회 측정이 끝났습니다. {next_rep}회 측정을 시작하세요.")
            return self.status

        if self.status.state == "COMPLETE":
            self.status.screen_text = "모든 측정이 끝났습니다. 결과를 확인하세요. 다시 측정하려면 재시작 버튼을 누르세요."
            return self.status

        return self.status

    def _invalidate(self, message: str) -> None:
        # Crucial: discard the current peak and restart from a stable neutral state.
        self.window.clear()
        self.status.state = "WAITING_STABLE"
        self.status.current_peak = 0.0
        self.status.target_value = 0.0
        self.status.opposite_value = 0.0
        self.status.invalid_reason = message
        self._said_stabilizing = False
        self._cooldown_frames = 0
        self._speak(message)

    def _make_result(self) -> Dict[str, Any]:
        peaks = self.status.peaks[:]
        mean_rom = statistics.mean(peaks) if peaks else 0.0
        sd = statistics.stdev(peaks) if len(peaks) > 1 else 0.0
        return {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "measurement": self.spec.display_name(),
            "motion_id": self.spec.motion_id,
            "reliability": self.spec.reliability,
            "clinical_note": self.spec.clinical_note,
            "reps": len(peaks),
            "peaks": peaks,
            "mean_rom": mean_rom,
            "sd": sd,
            "max_rom": max(peaks) if peaks else 0.0,
            "min_rom": min(peaks) if peaks else 0.0,
        }

    def result_as_txt(self) -> str:
        result = self.status.result or self._make_result()
        lines = [
            "ROM 3회 반복 분석 결과",
            "=" * 40,
            f"생성 시각: {result['created_at']}",
            f"측정 항목: {result['measurement']}",
            f"신뢰도/해석: {result['reliability']}",
        ]
        if result.get("clinical_note"):
            lines.append(f"주의: {result['clinical_note']}")
        lines += [
            "",
            f"측정 반복수: {result['reps']}회",
            f"1~3회 최고값: {', '.join(f'{v:.1f}' for v in result['peaks'])}°",
            f"평균 ROM: {result['mean_rom']:.1f}°",
            f"표준편차: {result['sd']:.1f}",
            f"최대값: {result['max_rom']:.1f}°",
            f"최소값: {result['min_rom']:.1f}°",
            "",
            "주의: 본 프로그램은 교육용/피드백용입니다. 임상 진단 또는 치료 결정에 직접 사용하기 전에는 별도 검증이 필요합니다.",
        ]
        return "\n".join(lines)

    def result_as_json(self) -> str:
        return json.dumps(self.status.result or {}, ensure_ascii=False, indent=2)

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

import av
import cv2
import numpy as np
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
import streamlit.components.v1 as components

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:  # pragma: no cover
    st_autorefresh = None

from pose_model import PoseEstimator
from rom_core import (
    categories,
    joints,
    motions,
    get_spec_by_id,
    compute_measurement,
    GuidedROMAnalyzer,
    MeasurementSpec,
)

APP_DIR = Path(__file__).parent
MODEL_PATH = APP_DIR / "pose_landmarker_full.task"
VOICE_JS_PATH = APP_DIR / "voice.js"


# -----------------------------------------------------------------------------
# Drawing helpers
# -----------------------------------------------------------------------------

def put_text(img: np.ndarray, text: str, xy: tuple[int, int], scale: float = 0.65, color=(255, 255, 255), bg=(20, 20, 20)) -> None:
    x, y = xy
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    cv2.rectangle(img, (x - 6, y - th - 8), (x + tw + 6, y + 7), bg, -1)
    cv2.putText(img, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)


def draw_line(img: np.ndarray, p1, p2, color=(0, 180, 255), thickness=3) -> None:
    cv2.line(img, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), color, thickness, cv2.LINE_AA)


def draw_point(img: np.ndarray, p, color=(0, 255, 0), radius=7) -> None:
    cv2.circle(img, (int(p[0]), int(p[1])), radius, color, -1, cv2.LINE_AA)


def draw_reference_guides(img: np.ndarray, measurement, status: Dict[str, Any]) -> None:
    """Draw green/red guide lines. Green means neutral is stable enough."""
    h, w = img.shape[:2]
    ok = bool(status.get("alignment_ok", False))
    color = (0, 200, 0) if ok else (0, 0, 255)
    # global center crosshair, useful for arranging patient posture
    cv2.line(img, (w // 2, 0), (w // 2, h), color, 2, cv2.LINE_AA)
    cv2.line(img, (0, h // 2), (w, h // 2), color, 2, cv2.LINE_AA)
    # local reference through the main joint or base point
    if measurement and measurement.points:
        p = measurement.points[0]
        cv2.line(img, (int(p[0]), 0), (int(p[0]), h), color, 1, cv2.LINE_AA)
        cv2.line(img, (0, int(p[1])), (w, int(p[1])), color, 1, cv2.LINE_AA)


# -----------------------------------------------------------------------------
# WebRTC video processor
# -----------------------------------------------------------------------------

class ROMVideoProcessor(VideoProcessorBase):
    def __init__(
        self,
        spec_id: str,
        side: str,
        reverse_direction: bool,
        mirror_video: bool,
        reps: int,
        stable_seconds: float,
        start_threshold: float,
        return_threshold: float,
        opposite_threshold: float,
        stability_angle_sd: float,
    ) -> None:
        self.spec: MeasurementSpec = get_spec_by_id(spec_id)
        self.side = side
        self.reverse_direction = reverse_direction
        self.mirror_video = mirror_video
        self.pose = PoseEstimator(MODEL_PATH)
        self.analyzer = GuidedROMAnalyzer(
            spec=self.spec,
            reps=reps,
            stable_seconds=stable_seconds,
            start_threshold=start_threshold,
            return_threshold=return_threshold,
            opposite_threshold=opposite_threshold,
            stability_angle_sd=stability_angle_sd,
            reverse_direction=reverse_direction,
        )
        self.lock = threading.Lock()
        self.latest: Dict[str, Any] = {
            "state": "init",
            "screen_text": "초기화 중",
            "voice_id": 0,
            "voice_text": "",
            "rep_count": 0,
            "peaks": [],
            "result": None,
            "alignment_ok": False,
            "target_value": 0.0,
            "opposite_value": 0.0,
            "current_peak": 0.0,
            "raw_angle": None,
            "valid": False,
            "message": "",
        }

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        # Keep processing reasonably light for cloud deployment.
        img = cv2.resize(img, (640, 480))
        if self.mirror_video:
            img = cv2.flip(img, 1)

        h, w = img.shape[:2]
        measurement = None
        result_status = None

        try:
            landmarks = self.pose.detect(img)
            if landmarks:
                measurement = compute_measurement(self.spec, self.side, landmarks, w, h)
                result_status = self.analyzer.update(measurement.raw_angle, measurement.valid)
                if measurement.valid:
                    for p1, p2 in measurement.lines:
                        draw_line(img, p1, p2)
                    for p in measurement.points:
                        draw_point(img, p)
                else:
                    put_text(img, measurement.message, (20, 90), 0.55, color=(255, 255, 255), bg=(0, 0, 180))
            else:
                result_status = self.analyzer.update(None, False)
                put_text(img, "No body detected", (20, 90), 0.65, color=(255, 255, 255), bg=(0, 0, 180))
        except Exception as exc:
            result_status = self.analyzer.status
            put_text(img, f"Processing error: {exc}", (20, 90), 0.52, color=(255, 255, 255), bg=(0, 0, 180))

        status_dict = self._status_to_dict(result_status)
        draw_reference_guides(img, measurement, status_dict)

        # Overlay panel
        state = status_dict.get("state", "")
        rep_count = status_dict.get("rep_count", 0)
        target = status_dict.get("target_value", 0.0)
        current_peak = status_dict.get("current_peak", 0.0)
        screen_text = status_dict.get("screen_text", "")

        put_text(img, self.spec.display_name(), (20, 32), 0.50, bg=(0, 80, 120))
        put_text(img, f"State: {state}   Reps: {rep_count}/{self.analyzer.reps}", (20, 62), 0.55, bg=(40, 40, 40))
        put_text(img, f"ROM: {target:.1f} deg   Peak: {current_peak:.1f} deg", (20, 420), 0.62, bg=(40, 40, 40))
        put_text(img, screen_text[:58], (20, 455), 0.50, bg=(40, 40, 40))

        if status_dict.get("result"):
            res = status_dict["result"]
            put_text(img, f"Mean ROM: {res['mean_rom']:.1f} deg  SD: {res['sd']:.1f}", (20, 390), 0.62, color=(255, 255, 255), bg=(0, 120, 0))

        with self.lock:
            self.latest.update(status_dict)
            if measurement is not None:
                self.latest["raw_angle"] = measurement.raw_angle
                self.latest["valid"] = measurement.valid
                self.latest["message"] = measurement.message
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def _status_to_dict(self, s) -> Dict[str, Any]:
        if s is None:
            return dict(self.latest)
        return {
            "state": s.state,
            "voice_id": s.voice_id,
            "voice_text": s.voice_text,
            "screen_text": s.screen_text,
            "rep_count": s.rep_count,
            "peaks": list(s.peaks),
            "current_peak": float(s.current_peak),
            "target_value": float(s.target_value),
            "opposite_value": float(s.opposite_value),
            "signed_change": float(s.signed_change),
            "neutral_angle": s.neutral_angle,
            "stable_progress": float(s.stable_progress),
            "result": s.result,
            "alignment_ok": bool(s.alignment_ok),
            "invalid_reason": s.invalid_reason,
        }

    def get_latest(self) -> Dict[str, Any]:
        with self.lock:
            return dict(self.latest)

    def get_result_txt(self) -> str:
        with self.lock:
            return self.analyzer.result_as_txt()

    def reset_analyzer(self) -> None:
        with self.lock:
            self.analyzer = GuidedROMAnalyzer(
                spec=self.spec,
                reps=self.analyzer.reps,
                stable_seconds=self.analyzer.stable_seconds,
                start_threshold=self.analyzer.start_threshold,
                return_threshold=self.analyzer.return_threshold,
                opposite_threshold=self.analyzer.opposite_threshold,
                stability_angle_sd=self.analyzer.stability_angle_sd,
                reverse_direction=self.reverse_direction,
            )


# -----------------------------------------------------------------------------
# Voice helper
# -----------------------------------------------------------------------------

def speak_in_browser(text: str, enabled: bool = True) -> None:
    if not enabled or not text:
        return
    js_template = VOICE_JS_PATH.read_text(encoding="utf-8") if VOICE_JS_PATH.exists() else ""
    escaped = json.dumps(text, ensure_ascii=False)
    html = f"""
    <script>{js_template}</script>
    <script>
      window.romSpeak({escaped});
    </script>
    """
    components.html(html, height=0, width=0)


# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------

st.set_page_config(page_title="ROM 실시간 관절각 측정", page_icon="🦴", layout="wide")

st.title("🦴 실시간 관절가동범위(ROM) 교육용 피드백 앱")
st.caption("단일 웹캠 + MediaPipe 기반 교육/피드백용 프로토타입입니다. 임상 진단용으로 사용하기 전에는 별도 검증이 필요합니다.")

if not MODEL_PATH.exists():
    st.error("pose_landmarker_full.task 파일이 앱 폴더에 없습니다. 모델 파일을 추가한 뒤 다시 실행하세요.")
    st.stop()

with st.sidebar:
    st.header("측정 설정")
    category = st.selectbox("대분류", categories(), index=0)
    joint = st.selectbox("관절", joints(category), index=0)
    specs = motions(category, joint)
    spec_labels = [s.label for s in specs]
    selected_label = st.selectbox("측정 동작", spec_labels, index=0)
    spec = specs[spec_labels.index(selected_label)]

    if spec.unsupported:
        st.warning(spec.guide)

    side = "right"
    if spec.side_required:
        side_kr = st.radio("측정 쪽", ["오른쪽", "왼쪽"], horizontal=True)
        side = "right" if side_kr == "오른쪽" else "left"

    st.markdown("---")
    mirror_video = st.checkbox("영상 좌우 반전(거울 모드)", value=True)
    reverse_direction = st.checkbox("방향 반전", value=False, help="선택한 방향과 반대로 판정되면 켜세요.")
    voice_enabled = st.checkbox("브라우저 음성 안내", value=True)

    st.markdown("---")
    reps = st.number_input("반복 횟수", min_value=1, max_value=10, value=3, step=1)
    stable_seconds = st.slider("중립 안정 시간(초)", 0.8, 4.0, 2.0, 0.2)
    start_threshold = st.slider("움직임 시작 기준각", 3.0, 25.0, 8.0, 1.0)
    return_threshold = st.slider("중립 복귀 기준각", 1.0, 10.0, 3.0, 0.5)
    opposite_threshold = st.slider("반대방향 오류 기준각", 2.0, 20.0, 5.0, 1.0)
    stability_angle_sd = st.slider("중립 안정 민감도", 0.5, 5.0, 1.8, 0.1)

    st.markdown("---")
    st.subheader("사용 안내")
    st.write(spec.guide)
    st.info(f"신뢰도/해석: {spec.reliability}")
    if spec.clinical_note:
        st.warning(spec.clinical_note)

    if st.button("측정 상태 초기화", use_container_width=True):
        st.session_state["reset_request"] = time.time()

# Update UI periodically while WebRTC is running.
if st_autorefresh is not None:
    st_autorefresh(interval=700, key="rom_autorefresh")

col_video, col_status = st.columns([1.45, 0.95], gap="large")

with col_video:
    st.subheader("실시간 카메라")
    if spec.unsupported:
        st.stop()

    factory_kwargs = dict(
        spec_id=spec.motion_id,
        side=side,
        reverse_direction=reverse_direction,
        mirror_video=mirror_video,
        reps=int(reps),
        stable_seconds=float(stable_seconds),
        start_threshold=float(start_threshold),
        return_threshold=float(return_threshold),
        opposite_threshold=float(opposite_threshold),
        stability_angle_sd=float(stability_angle_sd),
    )

    webrtc_key = f"rom-{spec.motion_id}-{side}-{mirror_video}-{reverse_direction}-{int(reps)}"
    ctx = webrtc_streamer(
        key=webrtc_key,
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=lambda: ROMVideoProcessor(**factory_kwargs),
        media_stream_constraints={"video": {"width": 640, "height": 480}, "audio": False},
        async_processing=True,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    )

with col_status:
    st.subheader("측정 상태")
    latest: Optional[Dict[str, Any]] = None
    processor = ctx.video_processor if ctx and ctx.video_processor else None
    if processor is not None:
        # Reset current processor if requested.
        if "reset_request" in st.session_state:
            processor.reset_analyzer()
            del st.session_state["reset_request"]
        latest = processor.get_latest()
    else:
        latest = None

    if latest is None:
        st.info("위 카메라 영역에서 START를 눌러 측정을 시작하세요. 브라우저가 카메라 권한을 요청하면 허용해야 합니다.")
    else:
        state = latest.get("state", "")
        rep_count = latest.get("rep_count", 0)
        alignment_ok = latest.get("alignment_ok", False)
        progress = latest.get("stable_progress", 0.0)
        target_value = latest.get("target_value", 0.0)
        current_peak = latest.get("current_peak", 0.0)
        opposite_value = latest.get("opposite_value", 0.0)

        st.metric("상태", state)
        st.metric("완료 반복", f"{rep_count}/{int(reps)}")
        st.progress(float(min(1.0, max(0.0, progress))))
        st.write("기준선:", "✅ 안정" if alignment_ok else "⏳ 안정 대기")
        st.metric("현재 선택방향 ROM", f"{target_value:.1f}°")
        st.metric("현재 최고값", f"{current_peak:.1f}°")
        if opposite_value >= opposite_threshold:
            st.error(f"반대방향 움직임 감지: {opposite_value:.1f}°")

        st.markdown("### 화면 안내")
        st.write(latest.get("screen_text", ""))

        peaks = latest.get("peaks", []) or []
        if peaks:
            st.markdown("### 기록된 최고값")
            st.write(", ".join(f"{v:.1f}°" for v in peaks))

        # Voice: speak once per new voice_id.
        voice_id = latest.get("voice_id", 0)
        voice_text = latest.get("voice_text", "")
        voice_session_key = f"last_voice_id_{webrtc_key}"
        last_voice_id = st.session_state.get(voice_session_key, -1)
        if voice_enabled and voice_id and voice_id != last_voice_id and voice_text:
            st.session_state[voice_session_key] = voice_id
            speak_in_browser(voice_text, enabled=True)

        result = latest.get("result")
        if result:
            st.success("3회 반복 ROM 분석 완료")
            st.metric("평균 ROM", f"{result['mean_rom']:.1f}°")
            st.metric("표준편차", f"{result['sd']:.1f}")
            c1, c2 = st.columns(2)
            c1.metric("최대값", f"{result['max_rom']:.1f}°")
            c2.metric("최소값", f"{result['min_rom']:.1f}°")
            txt = processor.get_result_txt() if processor is not None else ""
            st.download_button("TXT 결과 다운로드", data=txt, file_name="rom_result.txt", mime="text/plain", use_container_width=True)
            st.download_button("JSON 결과 다운로드", data=json.dumps(result, ensure_ascii=False, indent=2), file_name="rom_result.json", mime="application/json", use_container_width=True)

st.markdown("---")
st.markdown(
    """
**측정 흐름**: START → 중립자세 유지 → 기준선 2초 안정 → 음성 안내 후 선택한 방향으로 움직임 → 처음 위치로 복귀 → 3회 반복 평균 산출  
**중요**: 단일 웹캠 기반 2D/준3D landmark 추정 방식이므로 교육·피드백용으로 사용하세요. 임상 진단/치료 결정용으로 사용하려면 별도 타당도 검증이 필요합니다.
"""
)

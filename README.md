# ROM 실시간 관절가동범위 교육용 피드백 앱

Streamlit + streamlit-webrtc + MediaPipe PoseLandmarker 기반의 교육/피드백용 ROM 측정 프로토타입입니다.

## 중요한 변경점

이 Cloud-safe 버전은 `import cv2`를 사용하지 않습니다. 영상 표시와 기준선/landmark 표시는 Pillow로 처리합니다. Streamlit Cloud 또는 Python/VS Code가 설치되지 않은 사용자의 컴퓨터에서는 브라우저만으로 접속하도록 설계했습니다.

## 로컬 실행

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

## Streamlit Community Cloud 배포

1. GitHub 저장소에 이 폴더의 파일을 모두 업로드합니다.
2. Streamlit Cloud에서 앱을 생성합니다.
3. Python 버전은 3.12를 권장합니다.
4. `requirements.txt`와 `packages.txt`가 앱 진입 파일(`app.py`)과 같은 위치 또는 저장소 루트에 있어야 합니다.
5. 스마트폰/외부 네트워크에서 WebRTC 연결이 지연되면 TURN 서버가 필요할 수 있습니다. Twilio 사용 시 Secrets에 아래 값을 추가합니다.

```toml
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

## 사용 흐름

START → 중립자세 유지 → 기준선 안정 → 선택한 방향으로 움직임 → 처음 위치로 복귀 → 반복 평균 산출

## 주의

단일 웹캠 기반 2D/준3D landmark 추정 방식입니다. 교육·운동 피드백용으로 사용하고, 임상 진단/치료 결정용으로 사용하려면 별도 타당도 검증이 필요합니다.

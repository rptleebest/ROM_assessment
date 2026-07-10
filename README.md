# 실시간 관절가동범위(ROM) 교육용 피드백 앱 - Browser-only 버전

이 버전은 Streamlit Cloud 서버에서 Python MediaPipe/OpenCV/WebRTC를 실행하지 않습니다.  
스마트폰과 PC 브라우저 안에서 MediaPipe Web JavaScript가 직접 카메라 영상을 분석합니다.

## 장점

- 사용자는 Python, VS Code 설치가 필요 없습니다.
- `mediapipe`, `opencv-python`, `streamlit-webrtc`, `twilio`가 필요 없습니다.
- 서버에서 카메라 영상을 처리하지 않고, 브라우저 안에서 처리합니다.
- Streamlit Cloud에서 설치 실패가 적습니다.
- 스마트폰에서 `https://...streamlit.app` 주소로 접속해 사용할 수 있습니다.

## 파일 구성

```text
rom-streamlit-browseronly-v1/
├─ app.py
├─ requirements.txt
├─ packages.txt
├─ .streamlit/config.toml
└─ README.md
```

## 로컬 실행

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

로컬에서는 반드시 다음 주소로 접속하세요.

```text
http://localhost:8501
```

## Streamlit Cloud 배포

1. 이 폴더의 파일을 GitHub 저장소 루트에 업로드합니다.
2. Streamlit Community Cloud에서 `app.py`를 main file로 지정합니다.
3. Python 버전은 3.12 또는 기본값을 사용해도 됩니다. 이 버전은 Python MediaPipe를 사용하지 않습니다.
4. 배포 후 스마트폰에서는 반드시 `https://...streamlit.app` 주소를 Chrome/Samsung Internet/Safari에서 직접 여세요.

## 사용법

1. 측정 부위와 동작을 선택합니다.
2. `카메라/모델 시작` 버튼을 누릅니다.
3. 카메라 권한을 허용합니다.
4. 중립자세를 취하고 기준선이 초록색으로 2초간 안정될 때까지 유지합니다.
5. 음성 안내 후 선택한 방향으로 관절을 움직이고 처음 위치로 돌아옵니다.
6. 지정한 반복 횟수만큼 완료되면 평균 ROM 결과가 표시됩니다.
7. `TXT 결과 다운로드` 또는 `JSON 결과 다운로드`를 사용할 수 있습니다.

## 주의

- 단일 웹캠 기반 2D/준3D 추정 방식입니다.
- 교육·피드백용 프로토타입이며, 임상 진단 또는 치료 결정에 사용하려면 별도 타당도 검증이 필요합니다.
- 목 회전은 실제 CROM 각도가 아니라 단일 카메라 기반 참고값입니다.
- 손가락/발가락 개별 관절은 이 버전에서 지원하지 않습니다.

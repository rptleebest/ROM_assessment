# 실시간 관절가동범위(ROM) 교육용 피드백 앱

단일 웹캠 + Streamlit + WebRTC + MediaPipe PoseLandmarker 기반 교육/피드백용 ROM 측정 프로토타입입니다.

## 중요

- 임상 진단/치료 결정을 위한 의료기기 소프트웨어가 아닙니다.
- 단일 웹캠 기반 2D/준3D landmark 추정 방식이므로 교육용 피드백 및 동작 연습용으로 사용하세요.
- Streamlit Cloud 배포 시 Python 3.12를 권장합니다.
- 이 Cloud-safe 버전은 `cv2`를 사용하지 않습니다.
- `packages.txt`는 의도적으로 비워 두었습니다. 기존 저장소에 `libglib2.0-0`, `libgl1` 등이 들어 있으면 삭제하거나 빈 파일로 교체하세요.

## 로컬 실행

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속하세요.

## Streamlit Community Cloud 배포

1. GitHub 저장소에 이 폴더의 파일들을 업로드합니다.
2. Streamlit Cloud에서 Python version을 3.12로 설정합니다.
3. 앱 파일은 `app.py`로 지정합니다.
4. 기존 `packages.txt`에 시스템 패키지명이 들어 있다면 반드시 비우거나 삭제합니다.
5. 앱을 Clear cache 후 Redeploy 합니다.

## 스마트폰 사용

스마트폰에서는 반드시 `https://...streamlit.app` 주소로 접속해야 합니다. 카메라 권한을 허용하고 START를 누르세요.

스마트폰 또는 기관 네트워크에서 WebRTC 연결이 오래 걸리면 TURN 서버가 필요할 수 있습니다. Twilio 계정을 사용한다면 Streamlit Secrets에 아래 값을 설정하세요.

```toml
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```


## Streamlit Cloud: cv2 ImportError fix

MediaPipe Tasks imports `cv2` internally even though this project does not use OpenCV directly.
On Streamlit Cloud, `cv2` can fail to load if Linux shared libraries are missing.
This v3 package therefore includes `packages.txt` with Debian trixie-compatible package names:

```text
libgl1
libglib2.0-0t64
libsm6
libxext6
libxrender1
```

Do not use the old package name `libglib2.0-0` on the current Streamlit Cloud image, because it can trigger an unmet dependency error involving `libffi7`.

After pushing these files to GitHub, run **Manage app → Clear cache → Reboot/Redeploy** in Streamlit Cloud.


## v4 추가 변경

- Streamlit Cloud에서 MediaPipe 내부 `import cv2`가 실패하는 문제를 줄이기 위해 앱 폴더에 최소 `cv2.py` 호환 stub을 포함했습니다.
- 이 앱은 OpenCV 기능을 직접 사용하지 않고 PIL 기반으로 화면을 렌더링합니다.
- `packages.txt`는 빈 파일입니다. Cloud에서 apt 의존성 충돌이 생기면 기존 packages.txt 내용을 모두 삭제하세요.

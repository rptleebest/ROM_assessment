# 실시간 관절가동범위(ROM) 교육용 피드백 웹앱

단일 웹캠, Streamlit, streamlit-webrtc, MediaPipe PoseLandmarker를 이용해 선택한 관절 움직임의 실시간 각도와 3회 반복 평균 ROM을 표시하는 교육용/피드백용 웹앱입니다.

> 주의: 본 프로그램은 교육용/피드백용 프로토타입입니다. 임상 진단, 치료 결정, 공식 평가 기록에 사용하려면 별도의 정확도·신뢰도·타당도 검증이 필요합니다.

## 1. 포함 파일

```text
rom-streamlit-app/
├─ app.py                       # Streamlit 앱 화면과 WebRTC 영상 처리
├─ rom_core.py                  # 관절 선택, 각도 계산, 반복 측정 분석 로직
├─ pose_model.py                # MediaPipe PoseLandmarker 래퍼
├─ voice.js                     # 브라우저 음성 안내
├─ requirements.txt             # Python 의존성
├─ pose_landmarker_full.task    # MediaPipe pose 모델 파일
├─ .streamlit/config.toml       # Streamlit 설정
├─ .gitignore
└─ README.md
```

## 2. 로컬 실행 방법

Python 3.10~3.12 환경을 권장합니다. Python 3.13에서는 일부 패키지 호환성 문제가 생길 수 있습니다.

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

브라우저가 열리면 카메라 권한을 허용하고, 화면의 `START` 버튼을 누르면 측정이 시작됩니다.

## 3. 기본 사용 순서

1. 왼쪽 사이드바에서 `대분류 → 관절 → 측정 동작`을 선택합니다.
2. 좌/우측이 필요한 관절은 `측정 쪽`을 선택합니다.
3. 카메라 화면의 `START` 버튼을 누릅니다.
4. 중립 자세를 유지합니다.
5. 기준선이 초록색으로 약 2초 안정되면 음성 안내가 나옵니다.
6. 선택한 방향으로 관절을 움직이고 처음 위치로 돌아옵니다.
7. 3회 반복이 끝나면 평균 ROM, 표준편차, 최대값, 최소값이 표시됩니다.
8. `TXT 결과 다운로드` 또는 `JSON 결과 다운로드`를 눌러 결과를 저장할 수 있습니다.

## 4. 방향 판정 원리

이 앱은 선택한 방향의 움직임만 정상 ROM 반복으로 인정합니다.

예: `목 좌측 굴곡`을 선택한 경우

```text
중립 → 좌측 굴곡 → 중립 복귀 = 정상 1회
중립 → 우측 굴곡 → 중립 복귀 = 반대방향 오류, 기록하지 않음
기준선 맞추는 작은 움직임 = 반복 측정으로 인정하지 않음
```

방향이 반대로 판정되면 사이드바의 `방향 반전`을 켜고 다시 측정하세요.

## 5. 측정 가능/제한 부위

비교적 적합한 항목:

- 목 좌/우측 굴곡
- 무릎 굴곡/신전
- 팔꿈치 굴곡/신전

참고값으로 보는 항목:

- 목 회전
- 몸통 굴곡/신전, 좌우측 굴곡
- 어깨, 고관절, 손목, 발목

현재 미지원:

- 손가락 개별 관절: MediaPipe Hands 추가 필요
- 발가락 개별 관절: 일반 Pose 기반으로는 제한 큼

## 6. Streamlit Community Cloud 배포 방법

1. GitHub에 새 저장소를 만듭니다.
2. 이 폴더의 파일 전체를 저장소에 업로드합니다.
3. Streamlit Community Cloud에서 `New app` 또는 `Create app`을 선택합니다.
4. GitHub 저장소, 브랜치, `app.py`를 지정합니다.
5. 배포합니다.

배포 후 사용자는 링크로 접속해 브라우저에서 카메라 권한을 허용하면 사용할 수 있습니다.

## 7. 배포 시 주의

- `pose_landmarker_full.task` 파일이 저장소에 포함되어야 합니다.
- Streamlit Cloud에서 카메라가 작동하려면 사용자가 브라우저에서 카메라 권한을 허용해야 합니다.
- 기관/학교 네트워크에서 WebRTC 연결이 제한될 수 있습니다.
- 음성 안내는 브라우저의 Web Speech API를 사용하므로 브라우저/OS에 따라 음성 품질이 다릅니다.

## 8. 문제 해결

### 카메라가 나오지 않을 때

- 브라우저 주소창 왼쪽의 카메라 권한을 확인합니다.
- 다른 프로그램이 카메라를 사용 중이면 종료합니다.
- 새로고침 후 다시 `START`를 누릅니다.

### 음성이 나오지 않을 때

- 사이드바의 `브라우저 음성 안내`가 켜져 있는지 확인합니다.
- 브라우저 음소거, Windows/맥 출력 장치, 볼륨을 확인합니다.
- 일부 브라우저는 사용자의 클릭 이후에만 음성 재생을 허용합니다. `START`를 누른 뒤 다시 시도하세요.

### 반대 방향으로 측정될 때

- 사이드바의 `방향 반전`을 켠 뒤 다시 측정합니다.
- 영상 좌우 반전 여부도 함께 확인합니다.


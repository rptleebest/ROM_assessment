import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="실시간 ROM 교육용 피드백 앱",
    page_icon="🦴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("🦴 실시간 관절가동범위(ROM) 교육용 피드백 앱")
st.caption(
    "Browser-only 버전: 카메라 영상과 MediaPipe 자세 추정은 서버가 아니라 사용자 브라우저 안에서 처리됩니다. "
    "교육·피드백용 프로토타입이며 임상 진단용 사용 전에는 별도 검증이 필요합니다."
)

HTML = r'''
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0" />
  <style>
    :root {
      --bg: #ffffff;
      --panel: #f7f9fc;
      --line: #d9e1ec;
      --text: #1f2937;
      --muted: #6b7280;
      --primary: #2563eb;
      --green: #16a34a;
      --red: #dc2626;
      --amber: #d97706;
      --black: #111827;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: var(--bg);
    }
    .app {
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 18px;
      min-height: 760px;
    }
    .sidebar {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
      height: fit-content;
      position: sticky;
      top: 8px;
    }
    .main { min-width: 0; }
    .section-title {
      font-size: 16px;
      font-weight: 800;
      margin: 8px 0 10px;
    }
    label { display:block; font-weight:700; margin: 10px 0 5px; }
    select, input[type="number"], input[type="range"] {
      width: 100%;
      padding: 9px 10px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      background: white;
      font-size: 14px;
    }
    .row { display:flex; gap:10px; align-items:center; }
    .row > * { flex: 1; }
    .check-row {
      display:flex;
      align-items:center;
      gap:8px;
      margin: 9px 0;
      font-size: 14px;
    }
    .check-row input { width: 18px; height: 18px; }
    .btn {
      border: 0;
      border-radius: 10px;
      padding: 12px 14px;
      font-weight: 800;
      cursor:pointer;
      font-size: 15px;
    }
    .btn-primary { background: var(--primary); color:white; }
    .btn-gray { background:#e5e7eb; color:#111827; }
    .btn-red { background:#fee2e2; color:#991b1b; }
    .btn-green { background:#dcfce7; color:#166534; }
    .btn:disabled { opacity: .5; cursor:not-allowed; }
    .video-wrap {
      border: 1px solid var(--line);
      border-radius: 16px;
      background: #0b1020;
      overflow: hidden;
      position: relative;
      width: 100%;
      max-width: 980px;
    }
    canvas {
      width: 100%;
      display:block;
      background:#111827;
      aspect-ratio: 4 / 3;
    }
    video { display:none; }
    .status-grid {
      display:grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 12px 0;
      max-width: 980px;
    }
    .card {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: white;
      padding: 12px;
      min-height: 78px;
    }
    .card .label { font-size: 13px; color: var(--muted); font-weight: 700; }
    .card .value { font-size: 26px; font-weight: 900; margin-top: 4px; }
    .guide {
      border-radius: 14px;
      padding: 14px;
      margin: 10px 0 14px;
      max-width: 980px;
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #1e3a8a;
      font-weight: 700;
      line-height: 1.45;
    }
    .guide.good { background:#ecfdf5; border-color:#86efac; color:#166534; }
    .guide.bad { background:#fef2f2; border-color:#fecaca; color:#991b1b; }
    .guide.warn { background:#fffbeb; border-color:#fde68a; color:#92400e; }
    .results {
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      max-width: 980px;
      background: #fafafa;
      margin-top: 14px;
    }
    .result-line { font-size: 18px; font-weight: 800; margin: 4px 0; }
    .small { font-size: 13px; color: var(--muted); line-height: 1.45; }
    .pill {
      display:inline-block;
      padding: 4px 9px;
      border-radius: 999px;
      background:#e0f2fe;
      color:#075985;
      font-weight: 800;
      font-size: 12px;
    }
    .download-row { display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; }
    hr { border:0; border-top: 1px solid var(--line); margin:16px 0; }
    @media (max-width: 900px) {
      .app { grid-template-columns: 1fr; }
      .sidebar { position: static; }
      .status-grid { grid-template-columns: repeat(2, 1fr); }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="section-title">1. 측정 항목</div>
      <label for="category">대분류</label>
      <select id="category"></select>
      <label for="joint">관절</label>
      <select id="joint"></select>
      <label for="motion">측정 동작</label>
      <select id="motion"></select>

      <hr>
      <div class="section-title">2. 표시 및 판정</div>
      <div class="check-row"><input id="mirror" type="checkbox" checked><span>영상 좌우 반전(거울 모드)</span></div>
      <div class="check-row"><input id="directionReverse" type="checkbox"><span>방향 반전</span></div>
      <div class="check-row"><input id="voiceOn" type="checkbox" checked><span>브라우저 음성 안내</span></div>
      <div class="check-row"><input id="autoStart" type="checkbox" checked><span>기준선 안정 후 자동 측정 시작</span></div>

      <label for="repCount">반복 횟수</label>
      <input id="repCount" type="number" min="1" max="10" value="3" />
      <label for="stableSec">중립 안정 시간(초): <span id="stableSecVal">2.0</span></label>
      <input id="stableSec" type="range" min="0.5" max="4" step="0.1" value="2.0" />
      <label for="moveTh">움직임 시작 기준각(°): <span id="moveThVal">8</span></label>
      <input id="moveTh" type="range" min="3" max="30" step="1" value="8" />
      <label for="returnTh">중립 복귀 기준각(°): <span id="returnThVal">3</span></label>
      <input id="returnTh" type="range" min="1" max="12" step="1" value="3" />

      <hr>
      <div class="section-title">3. 실행</div>
      <button id="startBtn" class="btn btn-primary" style="width:100%;">카메라/모델 시작</button>
      <div style="height:8px;"></div>
      <button id="measureBtn" class="btn btn-green" style="width:100%;" disabled>측정 새로 시작</button>
      <div style="height:8px;"></div>
      <button id="stopBtn" class="btn btn-red" style="width:100%;" disabled>카메라 정지</button>
      <p class="small">스마트폰에서는 Chrome, Samsung Internet, Safari 등 일반 브라우저에서 HTTPS 주소로 열어 주세요. 카카오톡 내부 브라우저는 카메라 권한이 불안정할 수 있습니다.</p>
    </aside>

    <main class="main">
      <div id="topGuide" class="guide">카메라/모델 시작 버튼을 누른 뒤 카메라 권한을 허용하세요.</div>
      <div class="video-wrap">
        <video id="video" playsinline autoplay muted></video>
        <canvas id="canvas" width="960" height="720"></canvas>
      </div>

      <div class="status-grid">
        <div class="card"><div class="label">상태</div><div id="stateVal" class="value">대기</div></div>
        <div class="card"><div class="label">현재 ROM</div><div id="romVal" class="value">--°</div></div>
        <div class="card"><div class="label">반복</div><div id="repVal" class="value">0/3</div></div>
        <div class="card"><div class="label">현재 최고값</div><div id="peakVal" class="value">--°</div></div>
      </div>

      <div id="resultsBox" class="results" style="display:none;">
        <div class="pill">분석 결과</div>
        <div id="resultLines"></div>
        <div class="download-row">
          <button id="downloadTxt" class="btn btn-gray">TXT 결과 다운로드</button>
          <button id="downloadJson" class="btn btn-gray">JSON 결과 다운로드</button>
        </div>
      </div>

      <p class="small"><b>측정 흐름:</b> 중립자세 유지 → 기준선 안정 → 선택 방향으로 움직임 → 처음 위치로 복귀 → 반복 평균 산출</p>
      <p class="small"><b>중요:</b> 단일 웹캠 기반 교육/피드백용 추정입니다. 임상 진단·치료 결정에 사용하려면 별도 검증이 필요합니다.</p>
    </main>
  </div>

<script type="module">
import { FilesetResolver, PoseLandmarker } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22-rc.20250304/vision_bundle.mjs";

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

const UI = {
  category: document.getElementById('category'),
  joint: document.getElementById('joint'),
  motion: document.getElementById('motion'),
  mirror: document.getElementById('mirror'),
  directionReverse: document.getElementById('directionReverse'),
  voiceOn: document.getElementById('voiceOn'),
  autoStart: document.getElementById('autoStart'),
  repCount: document.getElementById('repCount'),
  stableSec: document.getElementById('stableSec'),
  stableSecVal: document.getElementById('stableSecVal'),
  moveTh: document.getElementById('moveTh'),
  moveThVal: document.getElementById('moveThVal'),
  returnTh: document.getElementById('returnTh'),
  returnThVal: document.getElementById('returnThVal'),
  startBtn: document.getElementById('startBtn'),
  measureBtn: document.getElementById('measureBtn'),
  stopBtn: document.getElementById('stopBtn'),
  topGuide: document.getElementById('topGuide'),
  stateVal: document.getElementById('stateVal'),
  romVal: document.getElementById('romVal'),
  repVal: document.getElementById('repVal'),
  peakVal: document.getElementById('peakVal'),
  resultsBox: document.getElementById('resultsBox'),
  resultLines: document.getElementById('resultLines'),
  downloadTxt: document.getElementById('downloadTxt'),
  downloadJson: document.getElementById('downloadJson'),
};

const LM = {
  nose:0, leftEar:7, rightEar:8,
  leftShoulder:11, rightShoulder:12, leftElbow:13, rightElbow:14, leftWrist:15, rightWrist:16,
  leftIndex:19, rightIndex:20,
  leftHip:23, rightHip:24, leftKnee:25, rightKnee:26, leftAnkle:27, rightAnkle:28,
  leftFootIndex:31, rightFootIndex:32,
};

const MOTIONS = {
  '척추': {
    '목': [
      {id:'neck_flex', label:'목 굴곡 - 측면 촬영', calc:'neckFlexExt', sign: 1, plane:'side', note:'측면에서 촬영합니다. 굴곡 방향이 반대로 표시되면 방향 반전을 체크하세요.'},
      {id:'neck_ext', label:'목 신전 - 측면 촬영', calc:'neckFlexExt', sign:-1, plane:'side', note:'측면에서 촬영합니다. 신전 방향이 반대로 표시되면 방향 반전을 체크하세요.'},
      {id:'neck_lat_left', label:'목 좌측 굴곡 - 정면 촬영', calc:'neckLateral', sign:-1, plane:'front', note:'정면에서 촬영합니다. 코와 양쪽 어깨 중심을 기준으로 합니다.'},
      {id:'neck_lat_right', label:'목 우측 굴곡 - 정면 촬영', calc:'neckLateral', sign: 1, plane:'front', note:'정면에서 촬영합니다. 코와 양쪽 어깨 중심을 기준으로 합니다.'},
      {id:'neck_rot_left', label:'목 좌측 회전 - 정면 촬영, 참고값', calc:'neckRotationProxy', sign:-1, plane:'front', proxy:true, note:'회전은 실제 CROM이 아니라 단일 카메라 참고값입니다.'},
      {id:'neck_rot_right', label:'목 우측 회전 - 정면 촬영, 참고값', calc:'neckRotationProxy', sign: 1, plane:'front', proxy:true, note:'회전은 실제 CROM이 아니라 단일 카메라 참고값입니다.'},
    ],
    '가슴/허리(몸통 통합)': [
      {id:'trunk_flex', label:'몸통 굴곡 - 측면 촬영', calc:'trunk', sign:1, plane:'side', note:'어깨 중심과 골반 중심의 기울기로 몸통 움직임을 봅니다.'},
      {id:'trunk_ext', label:'몸통 신전 - 측면 촬영', calc:'trunk', sign:-1, plane:'side', note:'어깨 중심과 골반 중심의 기울기로 몸통 움직임을 봅니다.'},
      {id:'trunk_lat_left', label:'몸통 좌측 굴곡 - 정면 촬영', calc:'trunk', sign:-1, plane:'front', note:'정면에서 어깨 중심과 골반 중심의 좌우 기울기를 봅니다.'},
      {id:'trunk_lat_right', label:'몸통 우측 굴곡 - 정면 촬영', calc:'trunk', sign:1, plane:'front', note:'정면에서 어깨 중심과 골반 중심의 좌우 기울기를 봅니다.'},
    ],
  },
  '팔': {
    '어깨': [
      {id:'shoulder_flex_r', label:'오른쪽 어깨 굴곡 - 측면 촬영', calc:'three', side:'right', parts:['elbow','shoulder','hip'], sign:1, plane:'side', note:'어깨-팔꿈치-고관절을 이용한 2D 참고각입니다.'},
      {id:'shoulder_flex_l', label:'왼쪽 어깨 굴곡 - 측면 촬영', calc:'three', side:'left', parts:['elbow','shoulder','hip'], sign:1, plane:'side', note:'어깨-팔꿈치-고관절을 이용한 2D 참고각입니다.'},
      {id:'shoulder_abd_r', label:'오른쪽 어깨 벌림 - 정면 촬영', calc:'three', side:'right', parts:['elbow','shoulder','hip'], sign:1, plane:'front', note:'정면 촬영에서 상완과 몸통 사이 각도를 봅니다.'},
      {id:'shoulder_abd_l', label:'왼쪽 어깨 벌림 - 정면 촬영', calc:'three', side:'left', parts:['elbow','shoulder','hip'], sign:1, plane:'front', note:'정면 촬영에서 상완과 몸통 사이 각도를 봅니다.'},
    ],
    '팔꿈치': [
      {id:'elbow_flex_r', label:'오른쪽 팔꿈치 굴곡', calc:'three', side:'right', parts:['shoulder','elbow','wrist'], sign:-1, plane:'any', note:'어깨-팔꿈치-손목 3점 각도입니다. 굴곡은 보통 각도 감소로 계산됩니다.'},
      {id:'elbow_flex_l', label:'왼쪽 팔꿈치 굴곡', calc:'three', side:'left', parts:['shoulder','elbow','wrist'], sign:-1, plane:'any', note:'어깨-팔꿈치-손목 3점 각도입니다. 굴곡은 보통 각도 감소로 계산됩니다.'},
    ],
    '손목': [
      {id:'wrist_ref_r', label:'오른쪽 손목 굴곡/폄 참고값', calc:'three', side:'right', parts:['elbow','wrist','index'], sign:1, plane:'any', proxy:true, note:'Pose 모델의 손 landmark는 제한적이므로 참고값입니다.'},
      {id:'wrist_ref_l', label:'왼쪽 손목 굴곡/폄 참고값', calc:'three', side:'left', parts:['elbow','wrist','index'], sign:1, plane:'any', proxy:true, note:'Pose 모델의 손 landmark는 제한적이므로 참고값입니다.'},
    ],
    '손가락': [
      {id:'unsupported_finger', label:'미지원 - 손가락 개별관절은 별도 Hands 모델 필요', unsupported:true, note:'손가락 MCP/PIP/DIP는 별도 Hands 모델이 필요합니다.'}
    ],
  },
  '다리': {
    '엉덩이': [
      {id:'hip_flex_r', label:'오른쪽 고관절 굴곡 - 측면 촬영', calc:'three', side:'right', parts:['shoulder','hip','knee'], sign:-1, plane:'side', note:'몸통 보상 움직임을 줄이고 다리만 움직이세요.'},
      {id:'hip_flex_l', label:'왼쪽 고관절 굴곡 - 측면 촬영', calc:'three', side:'left', parts:['shoulder','hip','knee'], sign:-1, plane:'side', note:'몸통 보상 움직임을 줄이고 다리만 움직이세요.'},
      {id:'hip_abd_r', label:'오른쪽 고관절 벌림 - 정면 촬영', calc:'three', side:'right', parts:['shoulder','hip','knee'], sign:1, plane:'front', note:'정면 촬영에서 몸통과 대퇴 사이 2D 각도입니다.'},
      {id:'hip_abd_l', label:'왼쪽 고관절 벌림 - 정면 촬영', calc:'three', side:'left', parts:['shoulder','hip','knee'], sign:1, plane:'front', note:'정면 촬영에서 몸통과 대퇴 사이 2D 각도입니다.'},
    ],
    '무릎': [
      {id:'knee_flex_r', label:'오른쪽 무릎 굴곡', calc:'three', side:'right', parts:['hip','knee','ankle'], sign:-1, plane:'side', note:'고관절-무릎-발목 3점 각도입니다.'},
      {id:'knee_flex_l', label:'왼쪽 무릎 굴곡', calc:'three', side:'left', parts:['hip','knee','ankle'], sign:-1, plane:'side', note:'고관절-무릎-발목 3점 각도입니다.'},
    ],
    '발목': [
      {id:'ankle_df_r', label:'오른쪽 발목 배굴/저굴 참고값', calc:'three', side:'right', parts:['knee','ankle','footIndex'], sign:1, plane:'side', proxy:true, note:'무릎-발목-발끝 landmark를 이용한 참고값입니다.'},
      {id:'ankle_df_l', label:'왼쪽 발목 배굴/저굴 참고값', calc:'three', side:'left', parts:['knee','ankle','footIndex'], sign:1, plane:'side', proxy:true, note:'무릎-발목-발끝 landmark를 이용한 참고값입니다.'},
    ],
    '발가락': [
      {id:'unsupported_toe', label:'미지원 - 발가락 개별관절은 일반 Pose로 제한', unsupported:true, note:'발가락 개별관절은 일반 Pose 모델만으로 정확히 측정하기 어렵습니다.'}
    ],
  }
};

let poseLandmarker = null;
let stream = null;
let running = false;
let lastVideoTime = -1;
let lastLandmarks = null;
let selectedMotion = null;
let neutralValue = null;
let state = 'idle';
let stableStart = null;
let peak = 0;
let reps = [];
let invalidSpoken = false;
let resultData = null;
let speechQueue = [];
let speaking = false;
let lastSpeakKey = '';
let lastSpeakTime = 0;

function speak(text, key='') {
  if (!UI.voiceOn.checked) return;
  const now = performance.now();
  if (key && key === lastSpeakKey && now - lastSpeakTime < 2500) return;
  lastSpeakKey = key; lastSpeakTime = now;
  speechQueue.push(text);
  processSpeechQueue();
}
function processSpeechQueue() {
  if (speaking || speechQueue.length === 0) return;
  if (!('speechSynthesis' in window)) return;
  speaking = true;
  const text = speechQueue.shift();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'ko-KR';
  u.rate = 1.0;
  u.pitch = 1.0;
  u.onend = () => { speaking = false; setTimeout(processSpeechQueue, 120); };
  u.onerror = () => { speaking = false; setTimeout(processSpeechQueue, 120); };
  window.speechSynthesis.speak(u);
}

function setGuide(text, mode='info') {
  UI.topGuide.textContent = text;
  UI.topGuide.className = 'guide' + (mode ? ' ' + mode : '');
}
function setStateLabel(text) { UI.stateVal.textContent = text; }
function fmt(v) { return Number.isFinite(v) ? v.toFixed(1) : '--'; }
function mean(arr) { return arr.reduce((a,b)=>a+b,0) / Math.max(arr.length,1); }
function sd(arr) { if (arr.length < 2) return 0; const m=mean(arr); return Math.sqrt(arr.reduce((s,x)=>s+(x-m)*(x-m),0)/(arr.length-1)); }
function clamp(x,a,b){ return Math.max(a, Math.min(b, x)); }

function populateControls() {
  UI.category.innerHTML = Object.keys(MOTIONS).map(c => `<option>${c}</option>`).join('');
  updateJointOptions();
}
function updateJointOptions() {
  const cat = UI.category.value;
  UI.joint.innerHTML = Object.keys(MOTIONS[cat]).map(j => `<option>${j}</option>`).join('');
  updateMotionOptions();
}
function updateMotionOptions() {
  const cat = UI.category.value;
  const joint = UI.joint.value;
  UI.motion.innerHTML = MOTIONS[cat][joint].map((m, i) => `<option value="${i}">${m.label}</option>`).join('');
  selectedMotion = MOTIONS[cat][joint][Number(UI.motion.value || 0)];
  setGuide(selectedMotion.note || '측정 항목을 선택하세요.', selectedMotion.unsupported ? 'warn' : 'info');
}
UI.category.addEventListener('change', updateJointOptions);
UI.joint.addEventListener('change', updateMotionOptions);
UI.motion.addEventListener('change', updateMotionOptions);
UI.stableSec.addEventListener('input', () => UI.stableSecVal.textContent = Number(UI.stableSec.value).toFixed(1));
UI.moveTh.addEventListener('input', () => UI.moveThVal.textContent = UI.moveTh.value);
UI.returnTh.addEventListener('input', () => UI.returnThVal.textContent = UI.returnTh.value);

function getPt(lms, idx) {
  const lm = lms[idx];
  if (!lm) return null;
  const v = lm.visibility ?? 1;
  if (v < 0.35) return null;
  let x = lm.x, y = lm.y;
  if (UI.mirror.checked) x = 1 - x;
  return {x, y, visibility:v};
}
function mid(a,b) { if (a && b) return {x:(a.x+b.x)/2, y:(a.y+b.y)/2}; return a || b || null; }
function dist(a,b){ return Math.hypot(a.x-b.x, a.y-b.y); }
function angleFromVertical(base, top) {
  const dx = top.x - base.x;
  const dyUp = base.y - top.y;
  return Math.atan2(dx, dyUp) * 180 / Math.PI;
}
function angle3(a,b,c) {
  const bax = a.x - b.x, bay = a.y - b.y;
  const bcx = c.x - b.x, bcy = c.y - b.y;
  const n1 = Math.hypot(bax,bay), n2 = Math.hypot(bcx,bcy);
  if (n1 < 1e-6 || n2 < 1e-6) return null;
  const cos = clamp((bax*bcx + bay*bcy)/(n1*n2), -1, 1);
  return Math.acos(cos) * 180 / Math.PI;
}
function partIdx(side, part) {
  const prefix = side === 'left' ? 'left' : 'right';
  const map = {
    shoulder: LM[prefix+'Shoulder'], elbow: LM[prefix+'Elbow'], wrist: LM[prefix+'Wrist'],
    index: LM[prefix+'Index'], hip: LM[prefix+'Hip'], knee: LM[prefix+'Knee'], ankle: LM[prefix+'Ankle'], footIndex: LM[prefix+'FootIndex']
  };
  return map[part];
}
function measure(lms, motion) {
  if (!motion || motion.unsupported) return {ok:false, reason:'미지원 항목'};
  let raw = null, points = [], lines = [];
  const nose = getPt(lms, LM.nose);
  const ls = getPt(lms, LM.leftShoulder), rs = getPt(lms, LM.rightShoulder);
  const lh = getPt(lms, LM.leftHip), rh = getPt(lms, LM.rightHip);
  const le = getPt(lms, LM.leftEar), re = getPt(lms, LM.rightEar);
  const shoulderMid = mid(ls, rs);
  const hipMid = mid(lh, rh);

  if (motion.calc === 'neckFlexExt') {
    const earMid = mid(le, re) || nose;
    if (!shoulderMid || !earMid) return {ok:false, reason:'목/어깨 landmark 불명확'};
    raw = angleFromVertical(shoulderMid, earMid);
    points = [shoulderMid, earMid]; lines = [[shoulderMid, earMid]];
  } else if (motion.calc === 'neckLateral') {
    if (!shoulderMid || !nose) return {ok:false, reason:'코/어깨 landmark 불명확'};
    raw = angleFromVertical(shoulderMid, nose);
    points = [shoulderMid, nose]; lines = [[shoulderMid, nose]];
  } else if (motion.calc === 'neckRotationProxy') {
    if (!nose || !le || !re) return {ok:false, reason:'코/귀 landmark 불명확'};
    const earMid = mid(le,re);
    const earWidth = dist(le,re);
    if (earWidth < 0.03) return {ok:false, reason:'귀 간격이 너무 작음'};
    raw = Math.atan2(nose.x - earMid.x, earWidth) * 180 / Math.PI;
    points = [nose, le, re, earMid]; lines = [[le,re],[earMid,nose]];
  } else if (motion.calc === 'trunk') {
    if (!shoulderMid || !hipMid) return {ok:false, reason:'어깨/골반 landmark 불명확'};
    raw = angleFromVertical(hipMid, shoulderMid);
    points = [hipMid, shoulderMid]; lines = [[hipMid, shoulderMid]];
  } else if (motion.calc === 'three') {
    const ids = motion.parts.map(p => partIdx(motion.side, p));
    const pts = ids.map(id => getPt(lms, id));
    if (pts.some(p => !p)) return {ok:false, reason:'관절 landmark 불명확'};
    raw = angle3(pts[0], pts[1], pts[2]);
    points = pts; lines = [[pts[0],pts[1]],[pts[1],pts[2]]];
  }
  if (raw === null || !Number.isFinite(raw)) return {ok:false, reason:'각도 계산 불가'};

  const effSign = (UI.directionReverse.checked ? -1 : 1) * (motion.sign || 1);
  const selectedRom = neutralValue === null ? 0 : effSign * (raw - neutralValue);
  const oppositeRom = neutralValue === null ? 0 : -selectedRom;
  const neutralOk = neutralGuideOk(lms, motion);
  return {ok:true, raw, points, lines, selectedRom, oppositeRom, neutralOk};
}
function neutralGuideOk(lms, motion) {
  const nose = getPt(lms, LM.nose);
  const ls = getPt(lms, LM.leftShoulder), rs = getPt(lms, LM.rightShoulder);
  const lh = getPt(lms, LM.leftHip), rh = getPt(lms, LM.rightHip);
  const le = getPt(lms, LM.leftEar), re = getPt(lms, LM.rightEar);
  const shoulderMid = mid(ls, rs);
  const hipMid = mid(lh, rh);
  if (!motion) return {ok:false, msg:'측정 항목 없음'};
  if (motion.plane === 'front') {
    if (!nose || !shoulderMid || !ls || !rs) return {ok:false, msg:'코와 양쪽 어깨가 보여야 합니다'};
    const noseAlign = Math.abs(nose.x - shoulderMid.x) < 0.08;
    const shoulderLevel = Math.abs(ls.y - rs.y) < 0.06;
    return {ok: noseAlign && shoulderLevel, msg: noseAlign && shoulderLevel ? '중립 기준선 OK' : '코를 어깨 중심에 맞추고 양쪽 어깨를 수평으로 유지하세요'};
  }
  if (motion.plane === 'side') {
    const headPt = mid(le,re) || nose;
    if (!headPt || !shoulderMid) return {ok:false, msg:'귀/코와 어깨가 보여야 합니다'};
    const headAlign = Math.abs(headPt.x - shoulderMid.x) < 0.10;
    return {ok: headAlign, msg: headAlign ? '중립 기준선 OK' : '귀/코가 어깨 중심선에 오도록 자세를 조정하세요'};
  }
  // any/limb: landmarks visible is enough for neutral guide
  return {ok:true, msg:'시작자세 landmark OK'};
}

function resetMeasurement(startImmediately=false) {
  neutralValue = null;
  stableStart = null;
  peak = 0;
  reps = [];
  invalidSpoken = false;
  resultData = null;
  UI.resultsBox.style.display = 'none';
  UI.repVal.textContent = `0/${UI.repCount.value}`;
  UI.peakVal.textContent = '--°';
  UI.romVal.textContent = '--°';
  state = startImmediately ? 'wait_neutral' : 'ready_idle';
  setStateLabel(startImmediately ? '중립 대기' : '준비');
  if (startImmediately) {
    speak('측정을 시작합니다. 중립 자세를 취해 주세요. 기준선이 안정되면 측정을 시작합니다.', 'measure_start');
    setGuide('중립자세를 취하고 기준선이 초록색으로 안정될 때까지 유지하세요.', 'info');
  }
}
function completeRep(value) {
  reps.push(value);
  peak = 0;
  const target = Number(UI.repCount.value);
  UI.repVal.textContent = `${reps.length}/${target}`;
  UI.peakVal.textContent = '--°';
  if (reps.length >= target) {
    state = 'complete';
    const m = mean(reps), s = sd(reps), mn = Math.min(...reps), mx = Math.max(...reps);
    resultData = {date:new Date().toISOString(), motion:selectedMotion.label, repetitions:reps, mean:m, sd:s, min:mn, max:mx, note:selectedMotion.proxy ? '참고값: 실제 임상 CROM 각도가 아닙니다.' : ''};
    UI.resultsBox.style.display = 'block';
    UI.resultLines.innerHTML = `
      <div class="result-line">평균 ROM: ${m.toFixed(1)}°</div>
      <div class="result-line">SD: ${s.toFixed(1)}° &nbsp; Max: ${mx.toFixed(1)}° &nbsp; Min: ${mn.toFixed(1)}°</div>
      <div class="small">반복 최고값: ${reps.map(x=>x.toFixed(1)).join(', ')}°</div>
      ${selectedMotion.proxy ? '<div class="small"><b>주의:</b> 이 항목은 실제 임상 각도가 아닌 참고값입니다.</div>' : ''}
    `;
    setGuide('모든 측정이 끝났습니다. 결과를 확인하세요.', 'good');
    setStateLabel('완료');
    speak(`모든 측정이 끝났습니다. 결과를 확인하세요. 평균 관절가동범위는 ${m.toFixed(0)}도입니다.`, 'complete');
  } else {
    state = 'wait_next_neutral';
    stableStart = null;
    setGuide(`${reps.length}회 측정이 끝났습니다. 다시 중립자세를 맞춰 주세요.`, 'good');
    setStateLabel('다음 중립');
    speak(`정상적으로 측정되었습니다. ${reps.length}회 측정이 끝났습니다. ${reps.length+1}회 측정을 위해 중립자세를 맞춰 주세요.`, 'rep_done_'+reps.length);
  }
}
function markInvalid(reason) {
  peak = 0;
  state = 'invalid_wait_neutral';
  stableStart = null;
  setGuide(reason + ' 이번 움직임은 기록하지 않습니다. 기준선을 다시 맞춰 주세요.', 'bad');
  setStateLabel('재정렬');
  speak(reason + ' 이번 움직임은 기록하지 않습니다. 기준선을 다시 맞춰 주세요.', 'invalid');
}
function updateState(meas) {
  const now = performance.now();
  const repTarget = Number(UI.repCount.value);
  const stableMs = Number(UI.stableSec.value) * 1000;
  const moveTh = Number(UI.moveTh.value);
  const returnTh = Number(UI.returnTh.value);
  UI.repVal.textContent = `${reps.length}/${repTarget}`;

  if (!meas.ok) {
    setGuide(meas.reason || 'landmark를 찾을 수 없습니다.', 'warn');
    return;
  }
  const targetRom = Math.max(0, meas.selectedRom);
  const oppRom = Math.max(0, meas.oppositeRom);
  UI.romVal.textContent = `${fmt(targetRom)}°`;
  UI.peakVal.textContent = peak > 0 ? `${fmt(peak)}°` : '--°';

  if (state === 'idle' || state === 'ready_idle' || state === 'complete') return;

  if (state === 'wait_neutral' || state === 'wait_next_neutral' || state === 'invalid_wait_neutral') {
    const guideOk = meas.neutralOk.ok;
    if (guideOk) {
      if (stableStart === null) {
        stableStart = now;
        speak('기준선이 안정되고 있습니다. 그대로 유지하세요.', 'stable_start');
      }
      const elapsed = (now - stableStart) / 1000;
      setGuide(`기준선 안정 중입니다. ${elapsed.toFixed(1)} / ${Number(UI.stableSec.value).toFixed(1)}초`, 'good');
      setStateLabel('중립 안정');
      if (now - stableStart >= stableMs) {
        neutralValue = meas.raw;
        peak = 0;
        invalidSpoken = false;
        state = 'ready_to_move';
        stableStart = null;
        const prefix = reps.length === 0 ? '이제 측정을 시작합니다.' : '기준선이 안정되었습니다.';
        setGuide(`${prefix} 선택한 방향으로 관절을 움직인 뒤 처음 위치로 돌아오세요.`, 'good');
        setStateLabel('움직임 시작');
        speak(`${prefix} 관절을 움직이세요. 끝 범위까지 움직인 후 처음 위치로 돌아오세요.`, 'ready_move_'+reps.length);
      }
    } else {
      stableStart = null;
      setGuide(meas.neutralOk.msg || '기준선을 맞춰 주세요.', 'warn');
      setStateLabel('중립 조정');
    }
    return;
  }

  if (state === 'ready_to_move') {
    if (oppRom >= moveTh) {
      markInvalid('선택한 방향과 반대 방향으로 움직였습니다.');
      return;
    }
    if (targetRom >= moveTh) {
      state = 'moving';
      peak = targetRom;
      setGuide('측정 중입니다. 끝 범위까지 움직인 후 처음 위치로 돌아오세요.', 'info');
      setStateLabel('측정 중');
    }
    return;
  }

  if (state === 'moving') {
    if (oppRom >= moveTh) {
      markInvalid('선택한 방향과 반대 방향으로 움직였습니다.');
      return;
    }
    peak = Math.max(peak, targetRom);
    setStateLabel('측정 중');
    UI.peakVal.textContent = `${fmt(peak)}°`;
    if (targetRom <= returnTh && peak >= moveTh) {
      if (!meas.neutralOk.ok) {
        markInvalid('복귀 자세의 기준선이 맞지 않습니다.');
        return;
      }
      completeRep(peak);
    }
  }
}

function draw(meas) {
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0,0,w,h);
  if (video.readyState >= 2) {
    if (UI.mirror.checked) {
      ctx.save(); ctx.translate(w,0); ctx.scale(-1,1); ctx.drawImage(video,0,0,w,h); ctx.restore();
    } else {
      ctx.drawImage(video,0,0,w,h);
    }
  } else {
    ctx.fillStyle = '#111827'; ctx.fillRect(0,0,w,h);
  }
  // Crosshair / neutral helper
  const guideOk = meas?.ok ? meas.neutralOk.ok : false;
  ctx.lineWidth = 4;
  ctx.strokeStyle = guideOk ? '#22c55e' : '#ef4444';
  ctx.beginPath(); ctx.moveTo(w/2,0); ctx.lineTo(w/2,h); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0,h*0.75); ctx.lineTo(w,h*0.75); ctx.stroke();
  if (meas?.ok) {
    ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 6;
    for (const ln of meas.lines) {
      ctx.beginPath(); ctx.moveTo(ln[0].x*w, ln[0].y*h); ctx.lineTo(ln[1].x*w, ln[1].y*h); ctx.stroke();
    }
    for (const p of meas.points) {
      ctx.fillStyle = '#86efac'; ctx.beginPath(); ctx.arc(p.x*w, p.y*h, 8, 0, Math.PI*2); ctx.fill();
    }
  }
  // Text overlay
  ctx.font = 'bold 28px system-ui, sans-serif';
  ctx.fillStyle = 'rgba(255,255,255,0.85)'; ctx.fillRect(14,14, Math.min(w-28, 760), 122);
  ctx.fillStyle = '#111827';
  const title = selectedMotion ? selectedMotion.label : '측정 항목';
  ctx.fillText(title, 30, 50);
  ctx.fillStyle = guideOk ? '#16a34a' : '#dc2626';
  ctx.fillText(meas?.ok ? (meas.neutralOk.msg || '') : '카메라/landmark 대기 중', 30, 90);
  ctx.fillStyle = '#111827';
  const romText = meas?.ok ? `ROM ${fmt(Math.max(0, meas.selectedRom))}°   Peak ${peak ? fmt(peak) : '--'}°   Rep ${reps.length}/${UI.repCount.value}` : 'START 후 중립자세를 맞추세요';
  ctx.fillText(romText, 30, 126);
}

async function initModel() {
  if (poseLandmarker) return;
  setGuide('MediaPipe 모델을 불러오는 중입니다. 처음 실행 시 시간이 걸릴 수 있습니다.', 'info');
  const vision = await FilesetResolver.forVisionTasks(
    'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22-rc.20250304/wasm'
  );
  poseLandmarker = await PoseLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task',
      delegate: 'GPU'
    },
    runningMode: 'VIDEO',
    numPoses: 1,
    minPoseDetectionConfidence: 0.5,
    minPosePresenceConfidence: 0.5,
    minTrackingConfidence: 0.5
  });
}
async function startCamera() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new Error('이 브라우저에서는 카메라 API가 허용되지 않았습니다. HTTPS 주소와 일반 브라우저를 사용하세요.');
  }
  stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: 'user', width: {ideal: 960}, height: {ideal: 720}, frameRate: {ideal: 24, max: 30} },
    audio: false
  });
  video.srcObject = stream;
  await video.play();
  const vw = video.videoWidth || 960, vh = video.videoHeight || 720;
  canvas.width = vw; canvas.height = vh;
}
async function startAll() {
  try {
    updateMotionOptions();
    if (selectedMotion?.unsupported) {
      setGuide(selectedMotion.note || '현재 지원하지 않는 항목입니다.', 'warn');
      return;
    }
    UI.startBtn.disabled = true;
    await initModel();
    await startCamera();
    running = true;
    UI.stopBtn.disabled = false; UI.measureBtn.disabled = false;
    resetMeasurement(UI.autoStart.checked);
    requestAnimationFrame(loop);
  } catch (e) {
    console.error(e);
    setGuide('카메라 또는 모델 시작 실패: ' + e.message, 'bad');
    UI.startBtn.disabled = false;
  }
}
function stopAll() {
  running = false;
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
  UI.startBtn.disabled = false; UI.stopBtn.disabled = true; UI.measureBtn.disabled = true;
  setGuide('카메라가 정지되었습니다.', 'info');
  setStateLabel('정지');
}
function loop() {
  if (!running) return;
  let meas = {ok:false, reason:'landmark 대기'};
  try {
    if (video.readyState >= 2 && poseLandmarker) {
      const now = performance.now();
      const result = poseLandmarker.detectForVideo(video, now);
      if (result.landmarks && result.landmarks.length > 0) {
        lastLandmarks = result.landmarks[0];
        meas = measure(lastLandmarks, selectedMotion);
        updateState(meas);
      }
    }
  } catch (e) {
    console.error(e);
    meas = {ok:false, reason:e.message || '분석 오류'};
  }
  draw(meas);
  requestAnimationFrame(loop);
}

function makeTxt() {
  if (!resultData) return '';
  return [
    '실시간 관절가동범위(ROM) 교육용 피드백 결과',
    `측정일시: ${resultData.date}`,
    `측정동작: ${resultData.motion}`,
    `반복값: ${resultData.repetitions.map(x=>x.toFixed(1)).join(', ')} deg`,
    `평균 ROM: ${resultData.mean.toFixed(1)} deg`,
    `표준편차: ${resultData.sd.toFixed(1)} deg`,
    `최대값: ${resultData.max.toFixed(1)} deg`,
    `최소값: ${resultData.min.toFixed(1)} deg`,
    resultData.note ? `주의: ${resultData.note}` : '',
    '',
    '주의: 단일 웹캠 기반 교육/피드백용 결과이며 임상 진단용으로 사용하려면 별도 검증이 필요합니다.'
  ].filter(Boolean).join('\n');
}
function download(filename, text, mime) {
  const blob = new Blob([text], {type:mime});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=filename; a.click();
  setTimeout(()=>URL.revokeObjectURL(url), 1000);
}
UI.downloadTxt.addEventListener('click', () => download('rom_result.txt', makeTxt(), 'text/plain;charset=utf-8'));
UI.downloadJson.addEventListener('click', () => download('rom_result.json', JSON.stringify(resultData, null, 2), 'application/json;charset=utf-8'));
UI.startBtn.addEventListener('click', startAll);
UI.measureBtn.addEventListener('click', () => resetMeasurement(true));
UI.stopBtn.addEventListener('click', stopAll);

populateControls();
resetMeasurement(false);
// Initial placeholder drawing
ctx.fillStyle = '#111827'; ctx.fillRect(0,0,canvas.width,canvas.height);
ctx.fillStyle = '#ffffff'; ctx.font = 'bold 34px system-ui, sans-serif';
ctx.fillText('카메라/모델 시작을 누르세요', 40, 80);
</script>
</body>
</html>
'''

components.html(HTML, height=1120, scrolling=True)

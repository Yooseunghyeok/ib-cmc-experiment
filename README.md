# IB-CMC 해석편향 측정 도구

문자메시지 상황에 대한 해석편향(Interpretation Bias in Computer-Mediated Communication)을
측정하는 Windows용 데스크톱 실험 프로그램. Python + PsychoPy로 제작.

`IB-CMC 제작요청서(260711 수정).pdf`를 기준으로 구현했다.

## 지금까지 된 것 / 아직 안 된 것 (공동작업자용 진행 상황)

### 완료 (2026-07-14 기준)
- 참가자 정보 입력 → 사전 설명 → 사전검사 → 대기화면 → 사후 설명 → 사후검사 → 종료화면까지 전체 흐름
- 사전/사후 각각 독립적으로 문항 무작위화, 홀짝 문항에 따른 온건/부정 제시 순서 규칙 구현
  (`sequence.py`, `tests/test_sequence.py`로 검증됨)
- 응답 저장: 클릭 즉시 세션별 JSON에 저장 + 통합 CSV(`data/all_responses.csv`)에 append
  (`storage.py`, `tests/test_storage.py`로 검증됨). Google Sheets 연동은 아직 없고,
  `ResultStorage` 인터페이스만 분리해둠 — 나중에 `GoogleSheetsStorage`를 구현해서
  `app.py`에서 주입만 바꾸면 됨.
- ESC → 종료 확인(Y/N) → 저장 후 종료 처리
- iPhone/Galaxy UI를 별도 클래스로 분리 (`ui/iphone_chat.py`, `ui/galaxy_chat.py`),
  말풍선 색상/프레임 등은 `config/settings.yaml`에서 조정 가능
- 채팅(상황+말풍선) 화면은 PsychoPy 도형으로 직접 그리지 않고, HTML/CSS로 만들어서
  헤드리스 브라우저로 미리 PNG로 구워둔 걸 `ImageStim`으로 띄우는 방식으로 변경함
  (아래 "채팅 이미지 만드는 법" 참고). 말풍선 각도, 헤더 아이콘, 아바타, 꼬리(tail)
  등을 PsychoPy 도형 API로 일일이 좌표 맞추는 것보다 훨씬 정확하고 빠르게 수정 가능함.
  아이폰/갤럭시 각각 다른 모양의 말풍선 꼬리까지 반영됨.
- **문항 22개 전체** `src/ib_cmc/questions.py`에 작성 완료, **채팅 이미지 44장**
  (22문항 × iphone/galaxy) `assets/chat/`에 전부 생성해서 커밋됨
- 말풍선 색상을 제작요청서 지정대로(상대=흰색, 나=노란색·카카오톡 스타일) 조정
- Windows DPI 배율(125/150/200%) 대응: `SetProcessDpiAwareness` 호출 + 실제 창 크기에
  맞춰 폰트/프레임/척도를 자동 스케일링(`config.apply_scale`)하도록 변경. 창은 모니터
  작업 영역(작업표시줄 제외)에 맞춰 자동으로 크게 뜨되 타이틀바(최소화/복원)는 유지됨
- **화면 검증 완료 (2026-07-14)**: `tools/capture_screens.py`(아래 참고)로 실제 PsychoPy
  창을 띄워 22문항 × iPhone/Galaxy × 온건/부정 = 88화면 + 부속 화면 5장을 전부 캡처해서
  눈으로 확인함. 해석문·척도 겹침 없음, 채팅 이미지 잘림 없음, 긴 문항(9, 14, 15, 17,
  20, 22번) 줄바꿈 정상. 참가자 ID 입력창 placeholder를 한국어로 바꿈
- **척도 라벨 한 줄 표시 (2026-07-14)**: 제작요청서 p.3 코멘트("글자 크기와 간격 수정하여
  숫자와 한글이 위아래로 간격이 일치하게, 한 줄로 읽히게")대로 1~5점 라벨의 강제 줄바꿈을
  없애고 글자 크기 축소(16→13)·간격 확대(130→160). 가장 긴 라벨/해석문 조합까지 겹침 없는
  것을 재캡처로 확인함
- **구글시트 연동 구현 완료**: `GoogleSheetsStorage`(gspread) + `CompositeStorage`.
  `config/settings.yaml`의 `google_sheets.enabled: true`로 켜면 로컬 저장에 더해 시트의
  `responses`(원자료)/`summary`(참가자별 사전·사후 × 온건·부정 합계·평균) 워크시트에도
  기록됨. 시트 전송 실패는 실험을 막지 않고(로컬은 항상 저장) 종료 시 재전송 시도.
  **서비스 계정 발급/공유 방법: `docs/google_sheets_setup.md`** — 아직 계정/시트 준비가
  안 되어 실제 시트로의 end-to-end 확인은 못 함 (mock 테스트는 통과)

### 검증이 더 필요한 부분 (수동 확인 필요)
화면 레이아웃은 위 캡처로 확인됐고, 아래는 상호작용이라 직접 `python main.py`로
한 바퀴 돌면서 확인이 필요함:
- 참가자 정보 입력 화면의 `TextBox2`(참가자 ID 입력창) 키보드 포커스/타이핑 동작
- ESC → 종료 확인(Y/N) 동작
- 대기화면 이후 "다른 활동 후 다시 스페이스바" 흐름이 실제 창 최소화/복귀 시에도 문제없는지
- 완주 후 `data/<참가자ID>/<세션ID>.json` + `data/all_responses.csv` 내용 확인

### 다음에 할 일 (제안)
1. 위 수동 확인 항목 한 바퀴 완주로 체크
2. 구글 서비스 계정 만들기 (`docs/google_sheets_setup.md` 따라하기) → 더미 참가자로
   시트에 값 들어오는지 end-to-end 확인
3. summary 시트의 합계/평균 중 연구 분석에 쓸 값 연구자에게 확인

## 프로젝트 구조

```
src/ib_cmc/
  app.py                 실험 흐름 상태 머신 + create_window + 저장소 조립(_build_storage)
  config.py               config/settings.yaml 로더
  models.py                 Question / SessionState / ResponseRecord
  questions.py               문항 데이터 (22개 전체)
  sequence.py                 무작위화 + 온건/부정 제시 순서 규칙
  storage.py                   ResultStorage + LocalFileStorage + GoogleSheetsStorage + CompositeStorage
  screens/                      화면별 모듈 (participant/instruction/experiment/waiting/complete/common)
  ui/                             base_chat + iphone_chat + galaxy_chat (assets/chat/ 이미지를 ImageStim으로 표시)
  chat_templates/                  render.py(HTML->PNG 생성 스크립트) + static/(아바타 이미지)

assets/chat/              문항별 채팅 화면 PNG (render.py로 생성됨, 커밋됨)
config/settings.yaml     창 크기, 폰트, UI별 위치/크기/색상, 구글시트 설정
tools/capture_screens.py  전체 화면을 클릭 없이 캡처하는 검증 스크립트 (아래 참고)
docs/google_sheets_setup.md  구글 서비스 계정 발급/공유 가이드
tests/                    test_sequence.py, test_storage.py
main.py                   실행 진입점
```

## 실행 방법

**anaconda base 같은 공용 환경에 바로 설치하지 말 것.** `psychopy`가 numpy를 강제로
올려버려서 그 환경에 있던 다른 패키지(예: scipy, gensim 등)가 깨질 수 있음 (실제로 겪음).
반드시 이 프로젝트 전용 가상환경을 만들어서 쓴다.

```powershell
# PowerShell 기준 (이미 .venv가 있으면 두 번째 줄부터)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest              # 단위 테스트 (sequence, storage) — 디스플레이 없어도 실행됨
python main.py       # 실제 실험 프로그램 실행 (PsychoPy 창)
```

(cmd에서는 `.\.venv\Scripts\Activate.ps1` 대신 `.venv\Scripts\activate.bat`,
git bash에서는 `source .venv/Scripts/activate`)

### 화면 검증용 스크린샷 캡처

측정 화면 88장(22문항 × iPhone/Galaxy × 온건/부정)과 부속 화면(참가자 입력/설명/
대기/종료)을 클릭 없이 자동으로 그려서 `data/preview/`에 PNG로 저장한다.
실제 실험과 동일한 창/자극 코드를 쓰므로 레이아웃 수치를 바꾼 뒤 확인할 때 유용함:

```powershell
python tools\capture_screens.py                      # 전체 88장 + 부속 화면
python tools\capture_screens.py --ui iphone          # iPhone 버전만
python tools\capture_screens.py --items 1,2,14       # 특정 문항만
python tools\capture_screens.py --no-aux             # 측정 화면만
```

`config/settings.yaml`에서 창 크기, 폰트, UI 위치/크기/색상을 조정할 수 있다.

창은 기본적으로(`window.fullscreen: false`) 모니터의 작업 영역(작업표시줄 제외)에
맞춰 자동으로 크게 뜨되, 일반 창모드라 타이틀바의 최소화/복원 버튼이 그대로 있다 —
대기화면에서 "다른 활동 후 스페이스바로 복귀" 흐름과 맞음. 진짜 전체화면(kiosk
모드, 최소화 불가)이 필요하면 `window.fullscreen: true`로 바꾸면 되는데, 그러면
창을 내렸다 올리는 게 안 되므로 특수한 경우가 아니면 권장하지 않는다.

`app.py`의 `run_experiment()`는 시작하자마자 `SetProcessDpiAwareness`를 호출해
Windows의 디스플레이 배율(125%/150%/200% 등) 문제를 미리 막는다. 이걸 안 하면
Windows가 "이 프로그램은 DPI를 모른다"고 판단해서 좌표를 실제 해상도의 절반 같은
값으로 알려주고, 그 크기로 만든 창을 다시 확대해서 그리는 바람에 타이틀바가
흐릿해지거나 거의 안 보이고 화면 전체를 뒤덮어 실질적으로 전체화면처럼 보이는
문제가 생긴다 (배율 200% 모니터에서 실제로 재현/확인함).

### Windows + Python 3.12에서 `python main.py` 실행 시 에러가 나면

`psychopy`가 Windows용으로 고정하는 `pyglet==1.4.11`이 Python 3.10+ 의 엄격해진 ctypes
타입 체크와 충돌해서, 글자를 그리려는 순간(`TextStim` 생성 시) 아래와 같은 에러로 죽는
경우가 있다 (실제로 이 환경에서 재현됨):

```
ctypes.ArgumentError: argument 5: TypeError: expected LP_c_ubyte instance instead of c_byte_Array_...
```

이건 이 프로젝트 코드 문제가 아니라 pyglet 자체의 알려진 버그. 가상환경 안의
`pyglet/font/win32.py`에서 `GDIPlusGlyphRenderer._create_bitmap`의 아래 한 줄을 고치면
해결된다 (venv를 새로 만들 때마다 다시 해줘야 함):

```python
# .venv/Lib/site-packages/pyglet/font/win32.py 안의 _create_bitmap 메서드
self._data = (ctypes.c_byte * (4 * width * height))()   # 원본
self._data = (ctypes.c_ubyte * (4 * width * height))()  # 수정
```

이 수정 후 실제로 창이 뜨고 참가자 정보 입력 화면까지 렌더링되는 것 확인함
(2026-07-13). 다만 이후 화면들(말풍선 UI, 사전/사후검사 등)을 실제로 끝까지
눈으로 확인하는 건 아직 안 했으니 "검증이 더 필요한 부분" 항목은 여전히 유효함.

## 채팅 이미지 만드는 법

문항 화면의 상황+말풍선 부분은 `assets/chat/q{item_id}_{iphone|galaxy}.png`를
그대로 띄우는 것이다. 이 이미지들은 `src/ib_cmc/chat_templates/render.py`가
`questions.py`와 `config/settings.yaml`(말풍선 색상/코너/아바타 등) 값으로 HTML을
만들어서 헤드리스 브라우저로 스크린샷 떠서 만든다.

**19문항 추가하거나 색상/스타일을 바꾸면 다시 돌려야 한다:**

```bash
pip install playwright
playwright install chromium   # 최초 1회, 브라우저 바이너리 다운로드 (300MB 정도)
PYTHONPATH=src python -m ib_cmc.chat_templates.render
```

(Windows PowerShell이면 `PYTHONPATH=src` 대신 `$env:PYTHONPATH="src"`를 먼저 실행)

`assets/chat/`의 결과물은 저장소에 커밋해두므로, 실험 프로그램을 그냥 실행만 할
사람은 `playwright`를 설치할 필요 없다 — 이미지를 새로 만들 때만 필요.

아이폰 아바타는 `src/ib_cmc/chat_templates/static/avatar_iphone.webp`(실제 아이폰
기본 연락처 아이콘)를 쓰고, 갤럭시 아바타는 `header_name`의 첫 글자를 원 안에 넣어서
자동 생성한다.

## 데이터 저장

- `data/<참가자ID>/<세션ID>.json` : 세션별 전체 응답 (클릭 즉시 저장, 중간에 꺼져도 보존)
- `data/all_responses.csv` : 모든 참가자·iPhone/Galaxy 버전 통합 결과 (한 시트)
- (선택) 구글 스프레드시트 : `config/settings.yaml`의 `google_sheets.enabled: true`면
  `responses`(원자료) / `summary`(참가자별 사전·사후 × 온건·부정 합계·평균) 워크시트에도
  자동 기록. 설정 방법은 `docs/google_sheets_setup.md`. 시트 전송 실패는 실험을 막지
  않으며 로컬 저장은 항상 유지된다.

각 응답 행에는 `session_id, participant_id, ui_version, phase(pre/post), item_id,
item_presentation_order, interpretation_type(benign/negative), interpretation_order(1/2),
score(1~5), answered_at, started_at, completed_at, completion_status`가 들어있다.

# IB-CMC 해석편향 측정 도구

문자메시지 상황에 대한 해석편향(Interpretation Bias in Computer-Mediated Communication)을
측정하는 Windows용 데스크톱 실험 프로그램. Python + PsychoPy로 제작.

`IB-CMC 제작요청서(260711 수정).pdf`를 기준으로 구현했다.

## 지금까지 된 것 / 아직 안 된 것 (공동작업자용 진행 상황)

### 완료
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

### 문항 데이터: 22개 중 3개만 우선 구현
- PDF에는 22문항 전체 텍스트가 있지만, 초기 개발/테스트 단계라 **문항 1, 2, 14 세 개만**
  `src/ib_cmc/questions.py`에 넣어둠.
- 나머지 19개 문항은 같은 `Question(...)` 형식으로 `QUESTIONS` 리스트에 추가하기만 하면 됨.
  (`item_id`의 홀짝만으로 순서 규칙이 자동 적용되므로 추가 시 순서 로직은 건드릴 필요 없음)
- 나의 채팅이 상대 채팅보다 먼저 오는 문항(예: 14번)은 `my_message_position="before"`로
  표시해야 함 (기본값은 `"after"`).

### 검증이 더 필요한 부분 (실제 PsychoPy 창을 띄워봐야 확인 가능)
이 환경에는 화면(디스플레이)이 없어서 PsychoPy GUI를 직접 띄워보지 못했다. 로직 테스트
(`pytest`)는 통과하지만 아래는 실제 실행하면서 눈으로 확인이 필요함:
- 말풍선 크기 계산(`ui/base_chat.py`의 `TextStim.boundingBox` 기반 자동 사이징)이 실제
  창에서 텍스트 길이에 따라 잘 맞는지
- `config/settings.yaml`의 위치/간격 값들이 1280x800 창 기준으로 잘 맞는지 (해상도 다르면
  조정 필요)
- 참가자 정보 입력 화면의 `TextBox2`(참가자 ID 입력창) 키보드 포커스/타이핑 동작
- 대기화면 이후 "다른 활동 후 다시 스페이스바" 흐름이 실제 창 최소화/복귀 시에도 문제없는지

### 다음에 할 일 (제안)
1. 실제 PsychoPy 창으로 한 번 완주해보고 레이아웃 수치 보정
2. 나머지 19문항 `questions.py`에 추가
3. `GoogleSheetsStorage` 구현 (gspread 등) 후 `app.py`에서 `LocalFileStorage` 대신 주입,
   혹은 둘 다 쓰는 `CompositeStorage`로 확장

## 프로젝트 구조

```
src/ib_cmc/
  app.py                 실험 흐름 상태 머신
  config.py               config/settings.yaml 로더
  models.py                 Question / SessionState / ResponseRecord
  questions.py               문항 데이터 (현재 3개)
  sequence.py                 무작위화 + 온건/부정 제시 순서 규칙
  storage.py                   ResultStorage 인터페이스 + LocalFileStorage
  screens/                      화면별 모듈 (participant/instruction/experiment/waiting/complete/common)
  ui/                             base_chat + iphone_chat + galaxy_chat

config/settings.yaml     창 크기, 폰트, UI별 위치/크기/색상 설정
tests/                    test_sequence.py, test_storage.py
main.py                   실행 진입점
```

## 실행 방법

```bash
pip install -r requirements.txt
pytest              # 단위 테스트 (sequence, storage)
python main.py       # 실제 실험 프로그램 실행 (PsychoPy 창)
```

`config/settings.yaml`에서 창 크기, 폰트, UI 위치/크기/색상을 조정할 수 있다.
실제 실험 시에는 `window.fullscreen: true`로 바꾸면 된다.

## 데이터 저장

- `data/<참가자ID>/<세션ID>.json` : 세션별 전체 응답 (클릭 즉시 저장, 중간에 꺼져도 보존)
- `data/all_responses.csv` : 모든 참가자·iPhone/Galaxy 버전 통합 결과 (한 시트)

각 응답 행에는 `session_id, participant_id, ui_version, phase(pre/post), item_id,
item_presentation_order, interpretation_type(benign/negative), interpretation_order(1/2),
score(1~5), answered_at, started_at, completed_at, completion_status`가 들어있다.

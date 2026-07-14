# 구글 스프레드시트 연동 설정 가이드

실험 응답을 로컬(JSON/CSV)에 더해 구글 스프레드시트에도 자동 기록하려면
아래 단계를 한 번만 해두면 된다. 소요 시간 10~15분, 비용 없음.

연동하면 시트에 워크시트 두 개가 자동으로 생긴다:

- **responses**: 응답 원자료 (로컬 `data/all_responses.csv`와 동일한 열, 클릭 즉시 한 행씩 추가)
- **summary**: 참가자(세션)별 한 행 — `사전(온건)/사전(부정)/사후(온건)/사후(부정)`
  각각의 합계·평균 (제작요청서 1번의 연결시트 형식)

> 시트 전송이 실패해도(인터넷 끊김 등) 실험은 멈추지 않고 로컬 저장으로 계속
> 진행되며, 실패한 행은 검사 종료 시점에 한 번 더 재전송을 시도한다.

## 1. Google Cloud 프로젝트 만들기

1. https://console.cloud.google.com 접속 (구글 계정 로그인)
2. 상단의 프로젝트 선택 → **새 프로젝트** → 이름은 아무거나 (예: `ib-cmc`) → 만들기

## 2. Google Sheets API 켜기

1. 왼쪽 메뉴 **API 및 서비스 → 라이브러리**
2. "Google Sheets API" 검색 → 클릭 → **사용(Enable)**
3. 같은 방법으로 "Google Drive API"도 사용 설정 (gspread가 시트를 URL로 열 때 필요)

## 3. 서비스 계정 + 키(JSON) 만들기

1. **API 및 서비스 → 사용자 인증 정보(Credentials)**
2. **+ 사용자 인증 정보 만들기 → 서비스 계정**
3. 이름 아무거나 (예: `ib-cmc-writer`) → 만들기 → 역할은 건너뛰어도 됨 → 완료
4. 만들어진 서비스 계정 클릭 → **키(Keys) 탭 → 키 추가 → 새 키 만들기 → JSON** → 만들기
   - JSON 파일이 자동 다운로드된다
5. 다운로드된 파일을 이 프로젝트의 `config/google_service_account.json`으로 옮기고 이름 변경

> ⚠️ 이 JSON 키는 비밀번호와 같다. 절대 커밋/공유하지 말 것
> (`.gitignore`에 이미 등록되어 있어 실수로 커밋되지는 않는다).

## 4. 스프레드시트 만들고 서비스 계정에 공유

1. https://sheets.google.com 에서 새 스프레드시트 생성 (이름 예: `IB-CMC 결과`)
2. `config/google_service_account.json`을 메모장으로 열어 `"client_email"` 값 복사
   (`...@....iam.gserviceaccount.com` 형태)
3. 스프레드시트 우측 상단 **공유** → 그 이메일을 붙여넣고 권한 **편집자**로 공유
   ("알림 보내기"는 체크 해제해도 됨)
4. 브라우저 주소창의 시트 URL 전체 복사

## 5. settings.yaml에 입력

`config/settings.yaml` 맨 아래 `google_sheets` 부분을 수정:

```yaml
google_sheets:
  enabled: true
  spreadsheet_url: "https://docs.google.com/spreadsheets/d/여기에_복사한_URL"
  credentials_path: "config/google_service_account.json"
```

## 6. 동작 확인

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

더미 참가자 ID(예: `test1`)로 몇 문항 응답해보고, 스프레드시트에
`responses` 행이 실시간으로 쌓이는지 확인한다. ESC로 중단하거나 끝까지
완주하면 `summary`에 집계 행이 생긴다. 확인 후 시트에서 test 행은 지우면 됨.

## 문제 해결

- **"구글시트 연결 실패 — 로컬 저장만 사용합니다"가 뜰 때**: 키 파일 경로,
  시트 URL, 서비스 계정 이메일로 공유했는지(편집자 권한) 순서로 확인.
- **`gspread` 모듈이 없다는 에러**: 가상환경에서 `pip install -r requirements.txt` 재실행.
- **summary의 합계/평균**: 각 범주는 22문항 × 1~5점이라 합계 범위는 22~110.
  연구 분석에 합계/평균 중 무엇을 쓸지는 연구자가 정하면 된다 (둘 다 기록됨).

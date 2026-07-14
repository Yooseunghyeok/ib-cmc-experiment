"""결과 저장 인터페이스 + 로컬 파일 / 구글시트 구현.

- LocalFileStorage: 세션별 JSON + 통합 CSV (항상 사용, 실험의 기본 저장소)
- GoogleSheetsStorage: 같은 내용을 구글 스프레드시트에도 기록
  (설정 방법은 docs/google_sheets_setup.md 참고)
- CompositeStorage: 위 둘을 묶되, 시트 전송 실패(네트워크 등)가
  실험 진행을 절대 막지 않도록 로컬 저장만 필수로 취급한다.
"""
from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from dataclasses import replace
from pathlib import Path

from .models import CSV_FIELDNAMES, ResponseRecord, SessionState


class ResultStorage(ABC):
    @abstractmethod
    def save_response(self, record: ResponseRecord) -> None:
        """응답 하나를 즉시 영구 저장한다 (중간에 프로그램이 꺼져도 남도록)."""

    @abstractmethod
    def finalize_session(self, session: SessionState) -> None:
        """세션 종료 시점의 completed_at/completion_status를 반영한다."""

    @abstractmethod
    def load_session(self, session_id: str) -> list[ResponseRecord]:
        """세션 JSON을 읽어 ResponseRecord 리스트로 복원한다."""


class LocalFileStorage(ResultStorage):
    """세션별 JSON 파일 + 전체 참가자를 모으는 통합 CSV로 저장한다."""

    def __init__(self, data_dir: Path, participant_id: str, session_id: str):
        self.data_dir = Path(data_dir)
        self.participant_id = participant_id
        self.session_id = session_id

        self.session_dir = self.data_dir / participant_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.json_path = self.session_dir / f"{session_id}.json"

        self.master_csv_path = self.data_dir / "all_responses.csv"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._records: list[ResponseRecord] = []

    def save_response(self, record: ResponseRecord) -> None:
        self._records.append(record)
        self._write_json()
        self._append_master_csv(record)

    def finalize_session(self, session: SessionState) -> None:
        updated: list[ResponseRecord] = []
        for record in self._records:
            updated.append(
                replace(
                    record,
                    completed_at=session.completed_at,
                    completion_status=session.completion_status,
                )
            )
        self._records = updated
        self._write_json()
        self._rewrite_master_csv_for_session(session)

    def load_session(self, session_id: str) -> list[ResponseRecord]:
        path = self.data_dir / self.participant_id / f"{session_id}.json"
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [ResponseRecord.from_dict(item) for item in raw]

    def csv_path(self) -> Path:
        return self.master_csv_path

    def json_file_path(self) -> Path:
        return self.json_path

    def _write_json(self) -> None:
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self._records], f, ensure_ascii=False, indent=2)

    def _append_master_csv(self, record: ResponseRecord) -> None:
        is_new_file = not self.master_csv_path.exists()
        with open(self.master_csv_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            if is_new_file:
                writer.writeheader()
            writer.writerow(record.to_dict())

    def _rewrite_master_csv_for_session(self, session: SessionState) -> None:
        """finalize 시점에 이 세션이 이미 마스터 CSV에 남긴 행들의
        completed_at/completion_status를 최신값으로 갱신한다."""
        if not self.master_csv_path.exists():
            return

        with open(self.master_csv_path, "r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            if row["session_id"] == session.session_id:
                row["completed_at"] = session.completed_at or ""
                row["completion_status"] = session.completion_status

        with open(self.master_csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)


ITEM_IDS = range(1, 23)
SUMMARY_SHEET = "summary"
SUMMARY_COLUMN_SPECS = (
    ("pre", "benign", "사전(온건)"),
    ("pre", "negative", "사전(부정)"),
    ("post", "benign", "사후 (온건)"),
    ("post", "negative", "사후 (부정)"),
)


def summary_sheet_fieldnames() -> list[str]:
    """summary 워크시트의 wide-format 헤더를 만든다.

    각 문항마다 사전(온건), 사전(부정), 사후 (온건), 사후 (부정) 순서로
    4개 점수 열을 배치한다.
    """
    return [
        "ID",
        *(
            f"{item_id} {label}"
            for item_id in ITEM_IDS
            for _phase, _itype, label in SUMMARY_COLUMN_SPECS
        ),
    ]


SUMMARY_FIELDNAMES = summary_sheet_fieldnames()


def summarize_records(records: list[ResponseRecord]) -> dict[str, int | str]:
    """문항별 사전/사후 × 온건/부정 점수를 summary 행으로 정리한다.

    summary 워크시트에는 참가자 ID와 22개 문항 × 4개 조건(사전(온건),
    사전(부정), 사후 (온건), 사후 (부정)) 점수 열을 저장한다. 아직 응답이
    없는 문항/조건은 빈 문자열로 남긴다.
    """
    summary: dict[str, int | str] = {field: "" for field in SUMMARY_FIELDNAMES}
    for record in records:
        for phase, interpretation_type, label in SUMMARY_COLUMN_SPECS:
            if record.phase == phase and record.interpretation_type == interpretation_type:
                summary[f"{record.item_id} {label}"] = record.score
                break
    return summary


class GoogleSheetsStorage(ResultStorage):
    """응답을 구글 스프레드시트에 기록한다.

    - `responses` 워크시트: 통합 CSV와 같은 long 포맷, 응답 즉시 한 행 append
    - `summary` 워크시트: 참가자별 한 행 — ID와 22개 문항 × 사전/사후 ×
      온건/부정 88개 점수 열, finalize 시 upsert

    네트워크 오류 등으로 전송이 실패한 행은 내부 큐에 쌓아뒀다가
    finalize_session에서 재전송을 시도한다. 이 클래스의 메서드는 예외를 밖으로
    던지지 않는다 — 시트 문제로 실험이 중단되면 안 되기 때문이다. (로컬 저장은
    CompositeStorage의 primary인 LocalFileStorage가 항상 별도로 수행한다.)
    """

    RESPONSES_SHEET = "responses"
    SUMMARY_SHEET = SUMMARY_SHEET

    def __init__(self, spreadsheet):
        """spreadsheet: gspread의 Spreadsheet 객체 (테스트에서는 fake 주입)."""
        self.spreadsheet = spreadsheet
        self._records: list[ResponseRecord] = []
        self._pending_rows: list[list] = []
        self._responses_ws = None
        self._summary_ws = None

    @classmethod
    def from_service_account(cls, spreadsheet_url: str, credentials_path: Path) -> "GoogleSheetsStorage":
        import gspread  # 실험 실행만 하는 환경에는 없을 수 있어 지연 import

        client = gspread.service_account(filename=str(credentials_path))
        return cls(client.open_by_url(spreadsheet_url))

    def save_response(self, record: ResponseRecord) -> None:
        self._records.append(record)
        row = [record.to_dict().get(f, "") for f in CSV_FIELDNAMES]
        try:
            self._flush_pending()
            self._responses_worksheet().append_row(row, value_input_option="RAW")
        except Exception as e:
            self._pending_rows.append(row)
            print(f"[GoogleSheetsStorage] 응답 전송 실패, 큐에 보관 후 재시도 예정: {e}")

    def finalize_session(self, session: SessionState) -> None:
        try:
            self._flush_pending()
            self._upsert_summary(session)
        except Exception as e:
            print(f"[GoogleSheetsStorage] finalize 전송 실패 (로컬 저장은 유지됨): {e}")

    def load_session(self, session_id: str) -> list[ResponseRecord]:
        raise NotImplementedError("세션 복원은 LocalFileStorage에서 수행한다")

    def _responses_worksheet(self):
        if self._responses_ws is None:
            self._responses_ws = self._ensure_worksheet(self.RESPONSES_SHEET, CSV_FIELDNAMES)
        return self._responses_ws

    def _summary_worksheet(self):
        if self._summary_ws is None:
            self._summary_ws = self._ensure_worksheet(self.SUMMARY_SHEET, SUMMARY_FIELDNAMES)
        return self._summary_ws

    def _ensure_worksheet(self, title: str, header: list[str]):
        try:
            ws = self.spreadsheet.worksheet(title)
        except Exception:
            ws = self.spreadsheet.add_worksheet(title=title, rows=1000, cols=len(header))
        if not ws.row_values(1):
            ws.append_row(header, value_input_option="RAW")
        return ws

    def _flush_pending(self) -> None:
        while self._pending_rows:
            self._responses_worksheet().append_row(self._pending_rows[0], value_input_option="RAW")
            self._pending_rows.pop(0)

    def _upsert_summary(self, session: SessionState) -> None:
        row_dict = summarize_records(self._records)
        row_dict["ID"] = session.participant_id
        row = [row_dict.get(f, "") for f in SUMMARY_FIELDNAMES]

        ws = self._summary_worksheet()
        id_col = ws.col_values(SUMMARY_FIELDNAMES.index("ID") + 1)
        try:
            row_index = id_col.index(session.participant_id) + 1
        except ValueError:
            ws.append_row(row, value_input_option="RAW")
        else:
            ws.update(f"A{row_index}", [row], value_input_option="RAW")


class CompositeStorage(ResultStorage):
    """LocalFileStorage(필수) + 부가 저장소(구글시트 등)를 함께 쓴다.

    primary(로컬) 실패는 그대로 전파하고 — 데이터가 어디에도 안 남으면 안 되므로 —
    secondary 실패는 삼켜서 실험 진행을 막지 않는다.
    """

    def __init__(self, primary: LocalFileStorage, secondary: ResultStorage):
        self.primary = primary
        self.secondary = secondary

    def save_response(self, record: ResponseRecord) -> None:
        self.primary.save_response(record)
        try:
            self.secondary.save_response(record)
        except Exception as e:
            print(f"[CompositeStorage] 부가 저장소 save_response 실패: {e}")

    def finalize_session(self, session: SessionState) -> None:
        self.primary.finalize_session(session)
        try:
            self.secondary.finalize_session(session)
        except Exception as e:
            print(f"[CompositeStorage] 부가 저장소 finalize_session 실패: {e}")

    def load_session(self, session_id: str) -> list[ResponseRecord]:
        return self.primary.load_session(session_id)

    def csv_path(self) -> Path:
        return self.primary.csv_path()

    def json_file_path(self) -> Path:
        return self.primary.json_file_path()
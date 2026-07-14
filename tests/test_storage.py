import csv
import json

import pytest

from ib_cmc.models import ResponseRecord, SessionState
from ib_cmc.storage import (
    CSV_FIELDNAMES,
    SUMMARY_FIELDNAMES,
    CompositeStorage,
    GoogleSheetsStorage,
    LocalFileStorage,
    summarize_records,
)


def _make_record(**overrides) -> ResponseRecord:
    base = dict(
        session_id="sess-1",
        participant_id="p1",
        ui_version="iphone",
        phase="pre",
        item_id=1,
        item_presentation_order=1,
        interpretation_type="negative",
        interpretation_order=1,
        score=3,
        answered_at="2026-07-13T10:00:00",
        started_at="2026-07-13T09:59:00",
        completed_at=None,
        completion_status="in_progress",
    )
    base.update(overrides)
    return ResponseRecord(**base)


def test_save_response_persists_immediately_before_finalize(tmp_path):
    storage = LocalFileStorage(tmp_path, participant_id="p1", session_id="sess-1")
    record = _make_record()

    storage.save_response(record)

    # finalize_session을 호출하기 전에도 JSON 파일에 이미 데이터가 남아 있어야 함
    # (프로그램이 중간에 꺼져도 데이터 보존)
    assert storage.json_file_path().exists()
    with open(storage.json_file_path(), "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert len(saved) == 1
    assert saved[0]["score"] == 3
    assert saved[0]["completion_status"] == "in_progress"


def test_json_save_and_restore_round_trip(tmp_path):
    storage = LocalFileStorage(tmp_path, participant_id="p1", session_id="sess-1")
    records = [
        _make_record(item_id=1, interpretation_order=1, interpretation_type="negative", score=2),
        _make_record(item_id=1, interpretation_order=2, interpretation_type="benign", score=4),
        _make_record(item_id=2, interpretation_order=1, interpretation_type="benign", score=5),
    ]
    for r in records:
        storage.save_response(r)

    restored = storage.load_session("sess-1")

    assert len(restored) == len(records)
    assert [r.score for r in restored] == [2, 4, 5]
    assert all(isinstance(r, ResponseRecord) for r in restored)


def test_finalize_session_updates_completion_fields(tmp_path):
    storage = LocalFileStorage(tmp_path, participant_id="p1", session_id="sess-1")
    storage.save_response(_make_record())

    session = SessionState(
        session_id="sess-1",
        participant_id="p1",
        ui_version="iphone",
        started_at="2026-07-13T09:59:00",
        completed_at="2026-07-13T10:30:00",
        completion_status="completed",
    )
    storage.finalize_session(session)

    restored = storage.load_session("sess-1")
    assert restored[0].completed_at == "2026-07-13T10:30:00"
    assert restored[0].completion_status == "completed"


def test_master_csv_combines_multiple_sessions(tmp_path):
    storage_a = LocalFileStorage(tmp_path, participant_id="p1", session_id="sess-1")
    storage_a.save_response(_make_record(participant_id="p1", session_id="sess-1", ui_version="iphone"))

    storage_b = LocalFileStorage(tmp_path, participant_id="p2", session_id="sess-2")
    storage_b.save_response(
        _make_record(participant_id="p2", session_id="sess-2", ui_version="galaxy", item_id=2)
    )

    master_csv = tmp_path / "all_responses.csv"
    assert master_csv.exists()
    with open(master_csv, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    participant_ids = {row["participant_id"] for row in rows}
    assert participant_ids == {"p1", "p2"}


def test_summarize_records_aggregates_by_phase_and_type():
    records = [
        _make_record(phase="pre", interpretation_type="benign", score=2),
        _make_record(phase="pre", interpretation_type="benign", score=4),
        _make_record(phase="pre", interpretation_type="negative", score=5),
        _make_record(phase="post", interpretation_type="benign", score=1),
    ]

    summary = summarize_records(records)

    assert summary["사전(온건) 합계"] == 6
    assert summary["사전(온건) 평균"] == 3.0
    assert summary["사전(부정) 합계"] == 5
    assert summary["사후(온건) 합계"] == 1
    # 응답이 하나도 없는 범주는 빈 문자열 (0으로 오해되지 않도록)
    assert summary["사후(부정) 합계"] == 0
    assert summary["사후(부정) 평균"] == ""


class FakeWorksheet:
    def __init__(self, fail_appends: int = 0):
        self.rows: list[list] = []
        self.fail_appends = fail_appends

    def append_row(self, row, value_input_option=None):
        if self.fail_appends > 0:
            self.fail_appends -= 1
            raise ConnectionError("네트워크 오류 (테스트)")
        self.rows.append(list(row))

    def row_values(self, index):
        return self.rows[index - 1] if len(self.rows) >= index else []

    def col_values(self, index):
        return [row[index - 1] if len(row) >= index else "" for row in self.rows]

    def update(self, range_name, values, value_input_option=None):
        row_index = int(range_name.lstrip("A")) - 1
        self.rows[row_index] = list(values[0])


class FakeSpreadsheet:
    def __init__(self, fail_appends: int = 0):
        self.worksheets: dict[str, FakeWorksheet] = {}
        self.fail_appends = fail_appends

    def worksheet(self, title):
        if title not in self.worksheets:
            raise KeyError(title)
        return self.worksheets[title]

    def add_worksheet(self, title, rows, cols):
        ws = FakeWorksheet(fail_appends=self.fail_appends)
        self.fail_appends = 0
        self.worksheets[title] = ws
        return ws


def _make_session(**overrides) -> SessionState:
    base = dict(
        session_id="sess-1",
        participant_id="p1",
        ui_version="iphone",
        started_at="2026-07-13T09:59:00",
        completed_at="2026-07-13T10:30:00",
        completion_status="completed",
    )
    base.update(overrides)
    return SessionState(**base)


def test_google_sheets_appends_response_rows_with_header():
    sheet = FakeSpreadsheet()
    storage = GoogleSheetsStorage(sheet)

    storage.save_response(_make_record(score=4))

    ws = sheet.worksheets[GoogleSheetsStorage.RESPONSES_SHEET]
    assert ws.rows[0] == CSV_FIELDNAMES
    assert len(ws.rows) == 2
    assert ws.rows[1][CSV_FIELDNAMES.index("score")] == 4


def test_google_sheets_finalize_writes_summary_row():
    sheet = FakeSpreadsheet()
    storage = GoogleSheetsStorage(sheet)
    storage.save_response(_make_record(phase="pre", interpretation_type="negative", score=5))
    storage.save_response(_make_record(phase="post", interpretation_type="benign", score=2))

    storage.finalize_session(_make_session())

    ws = sheet.worksheets[GoogleSheetsStorage.SUMMARY_SHEET]
    assert ws.rows[0] == SUMMARY_FIELDNAMES
    row = dict(zip(SUMMARY_FIELDNAMES, ws.rows[1]))
    assert row["participant_id"] == "p1"
    assert row["사전(부정) 합계"] == 5
    assert row["사후(온건) 합계"] == 2
    assert row["completion_status"] == "completed"


def test_google_sheets_finalize_upserts_existing_summary_row():
    sheet = FakeSpreadsheet()
    storage = GoogleSheetsStorage(sheet)
    storage.save_response(_make_record(score=3))

    storage.finalize_session(_make_session(completion_status="aborted", completed_at=None))
    storage.finalize_session(_make_session(completion_status="completed"))

    ws = sheet.worksheets[GoogleSheetsStorage.SUMMARY_SHEET]
    assert len(ws.rows) == 2  # 헤더 + 세션당 한 행 (중복 append 없음)
    row = dict(zip(SUMMARY_FIELDNAMES, ws.rows[1]))
    assert row["completion_status"] == "completed"


def test_google_sheets_queues_failed_rows_and_retries_on_finalize():
    sheet = FakeSpreadsheet(fail_appends=1)  # 첫 append(헤더)부터 실패
    storage = GoogleSheetsStorage(sheet)

    storage.save_response(_make_record(item_id=1, score=1))  # 실패 → 큐에 보관
    storage.finalize_session(_make_session())  # 재시도 성공

    ws = sheet.worksheets[GoogleSheetsStorage.RESPONSES_SHEET]
    scores = [row[CSV_FIELDNAMES.index("score")] for row in ws.rows[1:]]
    assert scores == [1]


class ExplodingStorage(GoogleSheetsStorage):
    def __init__(self):
        pass

    def save_response(self, record):
        raise ConnectionError("boom")

    def finalize_session(self, session):
        raise ConnectionError("boom")


def test_composite_storage_isolates_secondary_failures(tmp_path):
    local = LocalFileStorage(tmp_path, participant_id="p1", session_id="sess-1")
    composite = CompositeStorage(local, ExplodingStorage())

    composite.save_response(_make_record(score=2))  # 예외가 밖으로 나오면 안 됨
    composite.finalize_session(_make_session())

    restored = composite.load_session("sess-1")
    assert [r.score for r in restored] == [2]
    assert restored[0].completion_status == "completed"


def test_composite_storage_propagates_primary_failures(tmp_path):
    local = LocalFileStorage(tmp_path, participant_id="p1", session_id="sess-1")
    composite = CompositeStorage(local, GoogleSheetsStorage(FakeSpreadsheet()))

    local.json_path = tmp_path  # 디렉터리에 쓰게 만들어 강제로 실패시킴
    with pytest.raises(OSError):
        composite.save_response(_make_record())

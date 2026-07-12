import csv
import json

from ib_cmc.models import ResponseRecord, SessionState
from ib_cmc.storage import LocalFileStorage


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

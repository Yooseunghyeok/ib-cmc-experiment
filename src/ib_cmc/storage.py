"""결과 저장 인터페이스 + 로컬 파일 구현.

지금은 로컬 JSON/CSV로만 저장하지만, 나중에 구글시트 연동이 필요해지면
ResultStorage를 구현하는 GoogleSheetsStorage를 새로 만들어 app.py에서
주입하는 구현체만 바꾸면 된다 (인터페이스는 그대로 유지).
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

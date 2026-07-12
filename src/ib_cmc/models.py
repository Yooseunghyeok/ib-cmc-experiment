"""실험 데이터 모델."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, Optional

Phase = Literal["pre", "post"]
InterpretationType = Literal["benign", "negative"]
UiVersion = Literal["iphone", "galaxy"]
CompletionStatus = Literal["in_progress", "completed", "aborted"]


MyMessagePosition = Literal["before", "after"]


@dataclass(frozen=True)
class Question:
    item_id: int
    situation: str
    friend_message: str
    my_message: Optional[str]
    benign_interpretation: str
    negative_interpretation: str
    my_message_position: MyMessagePosition = "after"

    def interpretation_text(self, interpretation_type: InterpretationType) -> str:
        if interpretation_type == "benign":
            return self.benign_interpretation
        return self.negative_interpretation


@dataclass
class SessionState:
    session_id: str
    participant_id: str
    ui_version: UiVersion
    started_at: str
    completed_at: Optional[str] = None
    completion_status: CompletionStatus = "in_progress"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResponseRecord:
    session_id: str
    participant_id: str
    ui_version: UiVersion
    phase: Phase
    item_id: int
    item_presentation_order: int
    interpretation_type: InterpretationType
    interpretation_order: int
    score: int
    answered_at: str
    started_at: str
    completed_at: Optional[str]
    completion_status: CompletionStatus

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "ResponseRecord":
        return ResponseRecord(**data)


CSV_FIELDNAMES = [
    "session_id",
    "participant_id",
    "ui_version",
    "phase",
    "item_id",
    "item_presentation_order",
    "interpretation_type",
    "interpretation_order",
    "score",
    "answered_at",
    "started_at",
    "completed_at",
    "completion_status",
]

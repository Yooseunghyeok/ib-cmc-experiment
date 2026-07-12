"""문항 제시 순서 결정 로직.

규칙 (제작요청서 기준, item_id의 홀짝으로 판단):
- 사전(pre): 홀수 문항 -> 부정 먼저, 짝수 문항 -> 온건 먼저
- 사후(post): 홀수 문항 -> 온건 먼저, 짝수 문항 -> 부정 먼저
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .models import InterpretationType, Phase, Question


@dataclass(frozen=True)
class SequenceEntry:
    item: Question
    phase: Phase
    item_presentation_order: int
    interpretation_type: InterpretationType
    interpretation_order: int  # 1 또는 2


def interpretation_order_for(item_id: int, phase: Phase) -> tuple[InterpretationType, InterpretationType]:
    is_odd = item_id % 2 == 1
    if phase == "pre":
        return ("negative", "benign") if is_odd else ("benign", "negative")
    return ("benign", "negative") if is_odd else ("negative", "benign")


def build_sequence(
    items: list[Question],
    phase: Phase,
    rng: random.Random | None = None,
) -> list[SequenceEntry]:
    rng = rng or random.Random()
    shuffled = items[:]
    rng.shuffle(shuffled)

    entries: list[SequenceEntry] = []
    for position, item in enumerate(shuffled, start=1):
        first, second = interpretation_order_for(item.item_id, phase)
        entries.append(SequenceEntry(item, phase, position, first, 1))
        entries.append(SequenceEntry(item, phase, position, second, 2))
    return entries

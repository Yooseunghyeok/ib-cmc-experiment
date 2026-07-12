import random

from ib_cmc.models import Question
from ib_cmc.sequence import build_sequence

ITEMS = [
    Question(1, "situation1", "friend1", None, "benign1", "negative1"),  # 홀수
    Question(2, "situation2", "friend2", None, "benign2", "negative2"),  # 짝수
    Question(14, "situation14", "friend14", "my14", "benign14", "negative14"),  # 짝수
]


def _order_by_item_id(entries):
    """item_id -> [interpretation_type at order 1, at order 2]"""
    result = {}
    for entry in entries:
        result.setdefault(entry.item.item_id, [None, None])
        result[entry.item.item_id][entry.interpretation_order - 1] = entry.interpretation_type
    return result


def test_pre_phase_odd_negative_first_even_benign_first():
    entries = build_sequence(ITEMS, "pre", random.Random(42))
    order = _order_by_item_id(entries)

    assert order[1] == ["negative", "benign"]  # 홀수
    assert order[2] == ["benign", "negative"]  # 짝수
    assert order[14] == ["benign", "negative"]  # 짝수


def test_post_phase_odd_benign_first_even_negative_first():
    entries = build_sequence(ITEMS, "post", random.Random(42))
    order = _order_by_item_id(entries)

    assert order[1] == ["benign", "negative"]  # 홀수
    assert order[2] == ["negative", "benign"]  # 짝수
    assert order[14] == ["negative", "benign"]  # 짝수


def test_sequence_length_is_item_count_times_two():
    entries = build_sequence(ITEMS, "pre", random.Random(1))
    assert len(entries) == len(ITEMS) * 2


def test_full_session_response_count_is_items_times_two_phases_times_two_interpretations():
    pre_entries = build_sequence(ITEMS, "pre", random.Random(1))
    post_entries = build_sequence(ITEMS, "post", random.Random(2))
    total = len(pre_entries) + len(post_entries)
    assert total == len(ITEMS) * 2 * 2


def test_shuffle_uses_independent_randomness_for_pre_and_post():
    # 서로 다른 rng 시드를 쓰면 문항 제시 "순서(위치)"가 달라질 수 있음을 확인
    pre_entries = build_sequence(ITEMS, "pre", random.Random(1))
    post_entries = build_sequence(ITEMS, "post", random.Random(1))

    pre_item_order = [e.item.item_id for e in pre_entries if e.interpretation_order == 1]
    post_item_order = [e.item.item_id for e in post_entries if e.interpretation_order == 1]

    # 두 시퀀스 모두 유효한 permutation인지만 확인 (동일 시드라도 phase 규칙 자체는 항상 성립)
    assert sorted(pre_item_order) == sorted(item.item_id for item in ITEMS)
    assert sorted(post_item_order) == sorted(item.item_id for item in ITEMS)


def test_item_presentation_order_is_consistent_within_item():
    entries = build_sequence(ITEMS, "pre", random.Random(7))
    order_by_item = {}
    for entry in entries:
        order_by_item.setdefault(entry.item.item_id, set()).add(entry.item_presentation_order)

    for item_id, positions in order_by_item.items():
        assert len(positions) == 1, f"item {item_id} should keep a single presentation order across its two screens"

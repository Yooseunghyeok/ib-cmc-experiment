"""실험 문항 데이터.

지금은 제작요청서의 문항 1, 2, 14 세 개만 사용한다.
나머지 19개 문항을 추가할 때는 이 리스트에 Question을 더 넣기만 하면 되고,
sequence.py의 홀짝 규칙은 item_id 기준이라 그대로 작동한다.
"""
from __future__ import annotations

from .models import Question

QUESTIONS: list[Question] = [
    Question(
        item_id=1,
        situation="수업 시작 몇 분 전, 나는 친구에게 내 자리를 맡아달라고 문자를 보냈더니 친구에게 답장이 왔다.",
        friend_message="나 민규랑 앉아 있어.",
        my_message=None,
        benign_interpretation="친구는 내가 자리를 찾을 수 있도록 어디 앉아 있는지 알려주는 것이다.",
        negative_interpretation="친구가 나랑 같이 앉고 싶지 않아 하는 것이다.",
    ),
    Question(
        item_id=2,
        situation="어느 날 저녁, 친구에게서 문자가 하나 와 있었다.",
        friend_message="가능한 한 빨리 전화해 줄 수 있어?",
        my_message=None,
        benign_interpretation="나에게 말해주려고 하는 흥미로운 일이 있는 것이다.",
        negative_interpretation="나에게 말해줄 안 좋은 일이 있는 것이다.",
    ),
    Question(
        item_id=14,
        situation="나는 오늘 친구와 만나서 놀기로 계획되어 있어 친구에게 문자를 했다.",
        friend_message="네가 원하는 거 아무거나.",
        my_message="그래서 오늘 뭐 하고 싶어?",
        benign_interpretation="친구는 우리가 무엇을 하든 상관없이 다 좋다는 뜻이다.",
        negative_interpretation="친구는 별로 놀고 싶어 하지 않는다는 뜻이다.",
        my_message_position="before",
    ),
]

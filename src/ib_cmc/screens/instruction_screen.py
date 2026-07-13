"""설명문 화면: 텍스트 표시 후 스페이스바를 누르면 진행."""
from __future__ import annotations

from psychopy import visual

from ..config import AppConfig
from .common import wait_for_space

PRE_INSTRUCTION_TEXT = (
    "본 과제에서는 여러분은 일상에서 흔히 겪을 수 있는 친구와의 문자 메세지 대화 "
    "상황들을 살펴보게 될 겁니다. 화면에 제시되는 메세지 내용을 읽고 제시되는 해석들이 "
    "여러분의 마음에 얼마나 떠오르는지 점수를 매겨주시면 됩니다.\n\n"
    "이 과제에는 정답이 없습니다. 평소 여러분이 친구와 문자를 주고받을 때 느끼는 점을 "
    "바탕으로 가장 솔직하게 응답해 주시면 됩니다.\n\n"
    "깊게 고민하지 말고 여러분의 마음속에 '즉각적으로' 떠오르는 정도를 선택해 주세요.\n\n"
    "준비 되시면 스페이스바를 눌러주세요. 이후 실험이 시작됩니다."
)

POST_INSTRUCTION_TEXT = (
    "지금부터는 방금과 동일하게 일상에서 흔히 겪을 수 있는 친구와의 문자 메시지 대화 "
    "상황을 본 후 메시지 내용과 이어지는 해석들이 여러분의 마음속에 얼마나 떠오르는지 "
    "점수를 매겨주시면 됩니다.\n\n"
    "아까 체크했던 점수를 생각하기보다, 지금 문장을 읽으면서 마음속에 즉각적으로 "
    "떠오르는 '현재의 느낌' 그대로 편안하게 점수를 매겨주세요.\n\n"
    "아까 체크했던 점수와 동일하여도 되고 달라져도 괜찮습니다.\n\n"
    "이번 역시 정답은 없으며 솔직하게 깊게 고민하지 말고 여러분의 마음속에 '즉각적으로' "
    "떠오르는 정도를 선택해주세요.\n\n"
    "스페이스바를 누르면 시작됩니다."
)


def run_instruction_screen(win, config: AppConfig, text: str) -> None:
    font = config.font
    s = config.scale
    stim = visual.TextStim(
        win, text=text, pos=(0, 20 * s), color=font.color, font=font.name,
        height=font.size_instruction, wrapWidth=1000 * s, alignText="left",
    )

    def draw_frame() -> None:
        stim.draw()

    wait_for_space(win, config, draw_frame)

"""설명문 화면: 미리 구워둔 설명문 이미지를 표시하고 스페이스바를 누르면 진행.

제작요청서에 설명문 일부가 밑줄로 강조되어 있는데 PsychoPy 텍스트는 밑줄을
지원하지 않는다. 채팅 화면과 같은 방식으로 chat_templates/render.py가 아래
텍스트를 HTML로 렌더링해 assets/instructions/ 아래 PNG로 구워두고, 여기서는
그 이미지를 띄운다. 텍스트를 수정했으면 그 스크립트를 다시 돌려야 한다:

    .venv\\Scripts\\python -m ib_cmc.chat_templates.render instructions
"""
from __future__ import annotations

import re
from pathlib import Path

from psychopy import visual

from ..chat_templates.render import INSTRUCTION_DSF, instruction_image_path
from ..config import AppConfig
from .common import wait_for_space

# <u>...</u>는 제작요청서(260711 수정) 2절에서 밑줄로 강조된 부분.
PRE_INSTRUCTION_TEXT = (
    "본 과제에서 여러분은 일상에서 흔히 겪을 수 있는 친구와의 문자 메세지 대화 "
    "상황들을 살펴보게 될 겁니다. <u>화면에 제시되는 메세지 내용을 읽고 제시되는 해석들이 "
    "여러분의 마음에 얼마나 떠오르는지 점수를 매겨주시면 됩니다.</u>\n\n"
    "이 과제에는 정답이 없습니다. 평소 여러분이 친구와 문자를 주고받을 때 느끼는 점을 "
    "바탕으로 <u>가장 솔직하게</u> 응답해 주시면 됩니다.\n\n"
    "깊게 고민하지 말고 여러분의 마음속에 <u>'즉각적으로' 떠오르는 정도를 선택</u>해 주세요.\n\n"
    "준비 되시면 <span class=\"blue\">스페이스바를 눌러주세요. 이후 실험이 시작됩니다.</span>"
)

POST_INSTRUCTION_TEXT = (
    "지금부터는 방금과 동일하게 일상에서 흔히 겪을 수 있는 친구와의 문자 메시지 대화 "
    "상황을 본 후 메시지 내용과 이어지는 해석들이 여러분의 마음속에 얼마나 떠오르는지 "
    "점수를 매겨주시면 됩니다.\n\n"
    "아까 체크했던 점수를 생각하기보다, 지금 문장을 읽으면서 마음속에 '즉각적으로' "
    "떠오르는 '현재의 느낌' 그대로 편안하게 점수를 매겨주세요.\n\n"
    "아까 체크했던 점수와 동일하여도 되고 달라져도 괜찮습니다.\n\n"
    "이번 역시 정답은 없으며 솔직하게 깊게 고민하지 말고 여러분의 마음속에 '즉각적으로' "
    "떠오르는 정도를 선택해주세요.\n\n"
    "<span class=\"blue\">스페이스바를 누르면 시작됩니다.</span>"
)

INSTRUCTION_TEXTS = {"pre": PRE_INSTRUCTION_TEXT, "post": POST_INSTRUCTION_TEXT}


def build_instruction_stim(win, config: AppConfig, phase: str):
    s = config.scale
    image_path = Path(instruction_image_path(phase))
    if image_path.exists():
        from PIL import Image

        px_w, px_h = Image.open(image_path).size
        return visual.ImageStim(
            win, image=str(image_path),
            size=(px_w / INSTRUCTION_DSF * s, px_h / INSTRUCTION_DSF * s),
            pos=(0, 20 * s),
        )
    # 이미지를 아직 안 구운 개발 환경 폴백: 밑줄 없이 텍스트로 표시
    font = config.font
    text = re.sub(r"<[^>]+>", "", INSTRUCTION_TEXTS[phase])
    return visual.TextStim(
        win, text=text, pos=(0, 20 * s), color=font.color, font=font.name,
        height=font.size_instruction, wrapWidth=1000 * s, alignText="center",
    )


def run_instruction_screen(win, config: AppConfig, phase: str) -> None:
    stim = build_instruction_stim(win, config, phase)

    def draw_frame() -> None:
        stim.draw()

    wait_for_space(win, config, draw_frame)

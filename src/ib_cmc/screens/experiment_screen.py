"""측정 화면: 상황 + 채팅 + 해석문 + 1~5점 척도를 한 화면에 표시하고 클릭을 처리한다."""
from __future__ import annotations

from datetime import datetime

from psychopy import event, visual

from ..config import AppConfig
from ..models import InterpretationType, Question
from ..ui.base_chat import BaseChatRenderer, ChatMessage
from .common import confirm_exit

LIKERT_LABELS = [
    "전혀\n떠오르지 않음",
    "거의\n떠오르지 않음",
    "어느 정도\n떠오름",
    "상당히 많이\n떠오름",
    "확실히\n떠오름",
]


def _build_messages(question: Question) -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    if question.my_message and question.my_message_position == "before":
        messages.append(ChatMessage("me", question.my_message))
    messages.append(ChatMessage("friend", question.friend_message))
    if question.my_message and question.my_message_position == "after":
        messages.append(ChatMessage("me", question.my_message))
    return messages


def run_experiment_screen(
    win,
    config: AppConfig,
    chat_renderer: BaseChatRenderer,
    question: Question,
    interpretation_type: InterpretationType,
) -> tuple[int, str]:
    """점수(1~5)와 응답 시각(answered_at, ISO 문자열)을 반환한다."""
    font = config.font

    situation_stim = visual.TextStim(
        win, text=question.situation, pos=(0, 330), color=font.color, font=font.name,
        height=font.size_situation, wrapWidth=1000, alignText="center",
    )

    chat_stims = chat_renderer.build_stims(_build_messages(question))

    interpretation_text = question.interpretation_text(interpretation_type)
    prompt_stim = visual.TextStim(
        win, text="아래의 해석이 얼마나 마음속에 떠오르나요?", pos=(0, -160),
        color=font.color, font=font.name, height=font.size_chat,
    )
    interpretation_stim = visual.TextStim(
        win, text=interpretation_text, pos=(0, -200), color=font.color, font=font.name,
        height=font.size_interpretation, wrapWidth=1000, alignText="center",
    )

    likert = config.likert
    n = 5
    start_x = -likert.spacing * (n - 1) / 2
    boxes: list[visual.Rect] = []
    number_stims: list[visual.TextStim] = []
    label_stims: list[visual.TextStim] = []
    for i in range(n):
        x = start_x + i * likert.spacing
        boxes.append(
            visual.Rect(win, width=likert.box_size, height=likert.box_size, pos=(x, likert.y), lineColor="black", fillColor="white")
        )
        number_stims.append(
            visual.TextStim(win, text=str(i + 1), pos=(x, likert.y + likert.box_size), color=font.color, font=font.name, height=font.size_likert_number)
        )
        label_stims.append(
            visual.TextStim(win, text=LIKERT_LABELS[i], pos=(x, likert.y - likert.box_size - 6), color=font.color, font=font.name, height=font.size_likert_label, alignText="center", wrapWidth=likert.spacing)
        )

    mouse = event.Mouse(win=win)
    was_pressed = False

    event.clearEvents()
    while True:
        situation_stim.draw()
        for stim in chat_stims:
            stim.draw()
        prompt_stim.draw()
        interpretation_stim.draw()
        for box, number, label in zip(boxes, number_stims, label_stims):
            box.draw()
            number.draw()
            label.draw()
        win.flip()

        keys = event.getKeys()
        if "escape" in keys:
            confirm_exit(win, config)
            event.clearEvents()

        pressed = mouse.getPressed()[0]
        if pressed and not was_pressed:
            pos = mouse.getPos()
            for idx, box in enumerate(boxes):
                if box.contains(pos):
                    answered_at = datetime.now().isoformat()
                    return idx + 1, answered_at
        was_pressed = pressed

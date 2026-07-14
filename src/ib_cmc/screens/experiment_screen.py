"""측정 화면: 상황 + 채팅 + 해석문 + 1~5점 척도를 한 화면에 표시하고 클릭을 처리한다."""
from __future__ import annotations

from datetime import datetime

from psychopy import event, visual

from ..config import AppConfig
from ..models import InterpretationType, Question
from ..ui.base_chat import BaseChatRenderer
from .common import confirm_exit

# 제작요청서 p.3 코멘트: "글자 크기와 간격 수정하여 숫자와 한글이 위아래로
# 간격이 일치하게, 한 줄로 읽히게" — 라벨은 절대 줄바꿈 없이 한 줄이어야 한다.
LIKERT_LABELS = [
    "전혀 떠오르지 않음",
    "거의 떠오르지 않음",
    "어느 정도 떠오름",
    "상당히 많이 떠오름",
    "확실히 떠오름",
]


def build_experiment_stims(
    win,
    config: AppConfig,
    chat_renderer: BaseChatRenderer,
    question: Question,
    interpretation_type: InterpretationType,
) -> tuple[list, list]:
    """측정 화면 자극 전체를 만든다.

    반환: (draw_stims, boxes) — draw_stims는 그리기 순서대로 전체 자극,
    boxes는 클릭 판정용 1~5점 척도 박스(점수 순서대로). tools/capture_screens.py가
    클릭 루프 없이 화면만 그려서 스크린샷을 찍을 때도 이 함수를 그대로 쓴다.
    """
    font = config.font
    s = config.scale

    situation_stim = visual.TextStim(
        win, text=question.situation, pos=(0, 330 * s), color=font.color, font=font.name,
        height=font.size_situation, wrapWidth=1000 * s, alignText="center",
    )

    chat_stims = chat_renderer.build_stims(question)

    interpretation_text = question.interpretation_text(interpretation_type)
    prompt_stim = visual.TextStim(
        win, text="아래의 해석이 얼마나 마음속에 떠오르나요?", pos=(0, -160 * s),
        color=font.color, font=font.name, height=font.size_chat, wrapWidth=1000 * s,
    )
    interpretation_top_y = -185 * s
    interpretation_stim = visual.TextStim(
        win, text=interpretation_text, pos=(0, interpretation_top_y), color=font.color, font=font.name,
        height=font.size_interpretation, wrapWidth=1000 * s, alignText="center", anchorVert="top",
    )
    _, interpretation_height = interpretation_stim.boundingBox
    interpretation_bottom_y = interpretation_top_y - interpretation_height

    likert = config.likert
    # likert.y/spacing/box_size는 이미 config.scale이 적용된 값이다 (app.py의
    # apply_scale 참고). 해석문이 길어서 여러 줄로 줄바꿈되면 그 기본값보다 더
    # 아래로 밀어낸다 (문항이 짧으면 config 기본값을 그대로 쓴다).
    likert_y = min(likert.y, interpretation_bottom_y - 40 * s)
    n = 5
    start_x = -likert.spacing * (n - 1) / 2
    boxes: list[visual.Rect] = []
    number_stims: list[visual.TextStim] = []
    label_stims: list[visual.TextStim] = []
    for i in range(n):
        x = start_x + i * likert.spacing
        boxes.append(
            visual.Rect(win, width=likert.box_size, height=likert.box_size, pos=(x, likert_y), lineColor="black", fillColor="white")
        )
        number_stims.append(
            visual.TextStim(win, text=str(i + 1), pos=(x, likert_y + likert.box_size), color=font.color, font=font.name, height=font.size_likert_number)
        )
        label_stims.append(
            # wrapWidth를 라벨 길이보다 충분히 크게 줘서 두 줄로 꺾이지 않게 한다
            # (한 줄로 읽히는 건 요청서 요구사항). 겹침 방지는 likert.spacing과
            # size_likert_label 값(settings.yaml)으로 조절한다.
            visual.TextStim(win, text=LIKERT_LABELS[i], pos=(x, likert_y - likert.box_size - 6 * s), color=font.color, font=font.name, height=font.size_likert_label, alignText="center", wrapWidth=likert.spacing * 3)
        )

    draw_stims = [situation_stim, *chat_stims, prompt_stim, interpretation_stim]
    for box, number, label in zip(boxes, number_stims, label_stims):
        draw_stims += [box, number, label]
    return draw_stims, boxes


def run_experiment_screen(
    win,
    config: AppConfig,
    chat_renderer: BaseChatRenderer,
    question: Question,
    interpretation_type: InterpretationType,
) -> tuple[int, str]:
    """점수(1~5)와 응답 시각(answered_at, ISO 문자열)을 반환한다."""
    draw_stims, boxes = build_experiment_stims(
        win, config, chat_renderer, question, interpretation_type
    )

    mouse = event.Mouse(win=win)
    was_pressed = False

    event.clearEvents()
    while True:
        for stim in draw_stims:
            stim.draw()
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

"""측정 화면: 상황 + 채팅 + 해석문 + 1~5점 척도를 한 화면에 표시하고 클릭을 처리한다."""
from __future__ import annotations

from datetime import datetime

from psychopy import core, event, visual

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

# 수정요청(260821) 2번: '실제'라는 단어를 빼고 아래 문장으로 교체.
PROMPT_TEXT = "아래에 제시된 해석이 머릿속에 얼마나 떠오르는 것 같습니까?"

# 수정요청(260821) 5번: 네모칸을 누른 뒤 체크 표시를 이 시간만큼 보여주고 다음으로 넘어간다.
CHECK_FEEDBACK_SEC = 0.45


def _build_underlined_text(win, config: AppConfig, text: str, *, top_y: float, wrap_width: float, height: float):
    """가운데 정렬된 여러 줄 텍스트를 줄 단위로 만들고 각 줄 아래에 밑줄을 그린다.

    PsychoPy TextStim에는 밑줄 옵션이 없어서 wrapWidth에 맡기지 않고 여기서 직접
    어절 단위로 줄을 나눈 뒤, 줄마다 실제 렌더 폭을 재서 그만큼만 선을 긋는다.

    반환: (텍스트 자극들, 밑줄 자극들, 마지막 줄 아래 y좌표)
    """
    font = config.font
    s = config.scale

    probe = visual.TextStim(
        win, text="가", pos=(0, 0), color=font.color, font=font.name,
        height=height, wrapWidth=wrap_width * 10, alignText="center",
    )

    def measure(t: str) -> tuple[float, float]:
        probe.text = t
        w, h = probe.boundingBox
        return float(w), float(h)

    _, line_height = measure("가")

    lines: list[str] = []
    current = ""
    for word in text.split(" "):
        candidate = word if not current else f"{current} {word}"
        if not current or measure(candidate)[0] <= wrap_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_gap = line_height * 1.45
    underline_gap = 6 * s
    text_stims: list[visual.TextStim] = []
    underline_stims: list[visual.Line] = []
    for i, line in enumerate(lines):
        line_top = top_y - i * line_gap
        text_stims.append(
            visual.TextStim(
                win, text=line, pos=(0, line_top), color=font.color, font=font.name,
                height=height, wrapWidth=wrap_width * 10, alignText="center", anchorVert="top",
            )
        )
        line_width = measure(line)[0]
        underline_y = line_top - line_height - underline_gap
        underline_stims.append(
            visual.Line(
                win,
                start=(-line_width / 2, underline_y),
                end=(line_width / 2, underline_y),
                lineColor=font.color,
                lineWidth=max(1.5, 1.6 * s),
            )
        )

    bottom_y = top_y - (len(lines) - 1) * line_gap - line_height - underline_gap
    return text_stims, underline_stims, bottom_y


def build_check_stim(win, config: AppConfig, box: visual.Rect) -> visual.ShapeStim:
    """선택한 네모칸 안에 그릴 체크(✓) 표시. 폰트에 없는 글자일 수 있어 선으로 그린다."""
    x, y = box.pos
    b = float(box.width)
    return visual.ShapeStim(
        win,
        vertices=[
            (x - b * 0.30, y + b * 0.02),
            (x - b * 0.06, y - b * 0.28),
            (x + b * 0.34, y + b * 0.34),
        ],
        closeShape=False,
        lineColor="black",
        lineWidth=max(2.5, 3.0 * config.scale),
    )


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
        win, text=PROMPT_TEXT,
        pos=(0, -160 * s),
        color=font.color, font=font.name, height=font.size_prompt, wrapWidth=1000 * s,
    )
    # 수정요청(260821) 4번: 같은 문항에서 다음 해석으로 넘어간 걸 알 수 있도록
    # 해석문에 밑줄을 긋는다. PsychoPy TextStim은 밑줄을 지원하지 않아서 줄바꿈을
    # 직접 계산한 뒤 각 줄 아래에 선(Line)을 그린다.
    interpretation_top_y = -185 * s
    interpretation_stims, underline_stims, interpretation_bottom_y = _build_underlined_text(
        win, config, interpretation_text,
        top_y=interpretation_top_y, wrap_width=1000 * s, height=font.size_interpretation,
    )

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

    draw_stims = [situation_stim, *chat_stims, prompt_stim, *interpretation_stims, *underline_stims]
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
                    # 수정요청(260821) 5번: 어떤 칸을 눌렀는지 보이도록 체크 표시를
                    # 그린 화면을 잠깐 띄운 뒤 다음 화면으로 넘어간다.
                    check_stim = build_check_stim(win, config, box)
                    for stim in draw_stims:
                        stim.draw()
                    check_stim.draw()
                    win.flip()
                    core.wait(CHECK_FEEDBACK_SEC)
                    return idx + 1, answered_at
        was_pressed = pressed

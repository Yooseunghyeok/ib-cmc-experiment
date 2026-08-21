"""사전 과제 종료 후 한 번만 표시하는 고정점 응시 안내 화면."""
from __future__ import annotations

from psychopy import visual

from ..config import AppConfig
from .common import wait_for_space


def build_fixation_instruction_stims(win, config: AppConfig) -> list:
    """참고 이미지와 같은 검은 배경의 고정점 응시 안내 자극을 만든다."""
    font = config.font
    s = config.scale
    background = visual.Rect(
        win,
        width=win.size[0],
        height=win.size[1],
        pos=(0, 0),
        fillColor="black",
        lineColor="black",
    )
    fixation_message = visual.TextStim(
        win,
        text=(
            "잠시 후 화면 중앙의 고정점(+)에 이어 사진이 제시됩니다.\n"
            "고정점을 응시해 주십시오."
        ),
        pos=(0, 105 * s),
        color="white",
        font=font.name,
        height=font.size_instruction,
        bold=True,
        wrapWidth=1120 * s,
        alignText="center",
    )
    start_message = visual.TextStim(
        win,
        text="준비가 되면 스페이스바를 눌러 연습을 시작해 주십시오.",
        pos=(0, -115 * s),
        color="white",
        font=font.name,
        height=font.size_instruction,
        bold=True,
        wrapWidth=1120 * s,
        alignText="center",
    )
    return [background, fixation_message, start_message]


def run_fixation_instruction_screen(win, config: AppConfig) -> None:
    stims = build_fixation_instruction_stims(win, config)

    def draw_frame() -> None:
        for stim in stims:
            stim.draw()

    wait_for_space(win, config, draw_frame)

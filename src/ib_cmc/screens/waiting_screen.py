"""사전-사후 검사 사이 대기 화면: 흰 화면 + 안내문, 스페이스바를 누르면 진행."""
from __future__ import annotations

from psychopy import visual

from ..config import AppConfig
from .common import wait_for_space


def build_waiting_stim(win, config: AppConfig):
    font = config.font
    return visual.TextStim(
        win, text="모든 문항을 완료하였다면 옆의 종을 쳐주세요.", pos=(0, 0),
        color=font.color, font=font.name, height=font.size_instruction,
        wrapWidth=1000 * config.scale, alignText="center",
    )


def run_waiting_screen(win, config: AppConfig) -> None:
    stim = build_waiting_stim(win, config)

    def draw_frame() -> None:
        stim.draw()

    wait_for_space(win, config, draw_frame)

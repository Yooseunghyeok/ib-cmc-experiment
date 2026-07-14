"""검사 종료 화면: 종료 메시지 + 결과 저장 경로 표시."""
from __future__ import annotations

from pathlib import Path

from psychopy import event, visual

from ..config import AppConfig


def build_complete_stims(win, config: AppConfig, json_path: Path, csv_path: Path) -> list:
    font = config.font
    s = config.scale
    title = visual.TextStim(
        win, text="검사가 종료되었습니다.", pos=(0, 0),
        color=font.color, font=font.name, height=font.size_instruction, bold=True,
        wrapWidth=1000 * s,
    )
    return [title, paths_text, hint]


def run_complete_screen(win, config: AppConfig, json_path: Path, csv_path: Path) -> None:
    stims = build_complete_stims(win, config, json_path, csv_path)

    event.clearEvents()
    while True:
        for stim in stims:
            stim.draw()
        win.flip()
        if event.getKeys():
            return

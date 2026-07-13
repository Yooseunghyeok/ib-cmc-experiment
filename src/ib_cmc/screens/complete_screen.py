"""검사 종료 화면: 종료 메시지 + 결과 저장 경로 표시."""
from __future__ import annotations

from pathlib import Path

from psychopy import event, visual

from ..config import AppConfig


def run_complete_screen(win, config: AppConfig, json_path: Path, csv_path: Path) -> None:
    font = config.font
    s = config.scale
    title = visual.TextStim(
        win, text="검사가 종료되었습니다.", pos=(0, 60 * s),
        color=font.color, font=font.name, height=font.size_instruction, bold=True,
        wrapWidth=1000 * s,
    )
    paths_text = visual.TextStim(
        win,
        text=f"JSON 저장 경로:\n{json_path}\n\nCSV(통합) 저장 경로:\n{csv_path}",
        pos=(0, -60 * s),
        color=font.color,
        font=font.name,
        height=font.size_chat,
        wrapWidth=1000 * s,
        alignText="center",
    )
    hint = visual.TextStim(
        win, text="아무 키나 누르면 프로그램이 종료됩니다.", pos=(0, -260 * s),
        color=font.color, font=font.name, height=font.size_likert_label,
        wrapWidth=1000 * s,
    )

    event.clearEvents()
    while True:
        title.draw()
        paths_text.draw()
        hint.draw()
        win.flip()
        if event.getKeys():
            return

"""화면 공통 유틸: ESC 종료 확인, 스페이스바 대기."""
from __future__ import annotations

from psychopy import event, visual

from ..config import AppConfig


class ExperimentAborted(Exception):
    """참가자가 ESC 후 종료를 확정했을 때 발생시킨다."""


def confirm_exit(win, config: AppConfig) -> None:
    """ESC가 눌렸을 때 종료 여부를 물어본다. Y면 ExperimentAborted를 던진다."""
    font = config.font
    overlay_bg = visual.Rect(win, width=760, height=280, fillColor="white", lineColor="black", lineWidth=2)
    message = visual.TextStim(
        win,
        text="정말 종료하시겠습니까?\n\nY : 예 (종료하고 저장)      N : 아니오 (계속 진행)",
        pos=(0, 0),
        color="black",
        font=font.name,
        height=font.size_instruction,
        wrapWidth=700,
        alignText="center",
    )
    event.clearEvents()
    while True:
        overlay_bg.draw()
        message.draw()
        win.flip()
        keys = event.getKeys()
        if "y" in keys:
            raise ExperimentAborted()
        if "n" in keys or "escape" in keys:
            return


def wait_for_space(win, config: AppConfig, draw_frame) -> None:
    """draw_frame()이 매 프레임 화면을 그리고, 스페이스바가 눌리면 반환한다.
    ESC가 눌리면 confirm_exit()으로 종료 여부를 확인한다."""
    event.clearEvents()
    while True:
        draw_frame()
        win.flip()
        keys = event.getKeys()
        if "space" in keys:
            return
        if "escape" in keys:
            confirm_exit(win, config)

"""참가자 정보 입력 화면: 참가자 ID + UI 버전(iPhone/Galaxy) 선택."""
from __future__ import annotations

from psychopy import event, visual

from ..config import AppConfig
from ..models import UiVersion
from .common import confirm_exit


def run_participant_screen(win, config: AppConfig) -> tuple[str, UiVersion]:
    font = config.font
    s = config.scale

    title = visual.TextStim(
        win, text="참가자 정보를 입력해주세요", pos=(0, 260 * s),
        color=font.color, font=font.name, height=font.size_instruction, bold=True,
        wrapWidth=1000 * s,
    )
    id_label = visual.TextStim(
        win, text="참가자 ID", pos=(-320 * s, 140 * s),
        color=font.color, font=font.name, height=font.size_chat, wrapWidth=400 * s,
    )
    id_box = visual.TextBox2(
        win, text="", font=font.name, letterHeight=font.size_chat,
        pos=(60 * s, 140 * s), size=(320 * s, 50 * s), borderColor="black", borderWidth=1,
        fillColor="white", color="black", editable=True, alignment="left",
    )

    ui_label = visual.TextStim(
        win, text="UI 버전 선택", pos=(-320 * s, 40 * s),
        color=font.color, font=font.name, height=font.size_chat, wrapWidth=400 * s,
    )
    iphone_btn = visual.Rect(win, width=180 * s, height=60 * s, pos=(-90 * s, -30 * s), lineColor="black", fillColor="white")
    iphone_text = visual.TextStim(win, text="iPhone", pos=(-90 * s, -30 * s), color="black", font=font.name, height=font.size_chat)
    galaxy_btn = visual.Rect(win, width=180 * s, height=60 * s, pos=(120 * s, -30 * s), lineColor="black", fillColor="white")
    galaxy_text = visual.TextStim(win, text="Galaxy", pos=(120 * s, -30 * s), color="black", font=font.name, height=font.size_chat)

    start_btn = visual.Rect(win, width=200 * s, height=60 * s, pos=(0, -300 * s), lineColor="black", fillColor="white")
    start_text = visual.TextStim(win, text="시작", pos=(0, -300 * s), color="black", font=font.name, height=font.size_chat, bold=True)

    hint = visual.TextStim(
        win, text="ID를 입력하고 UI 버전을 선택한 뒤 [시작] 버튼을 클릭해주세요.",
        pos=(0, -200 * s), color=font.color, font=font.name, height=font.size_likert_label,
        wrapWidth=1000 * s,
    )
    error_text = visual.TextStim(
        win, text="", pos=(0, -240 * s), color="red", font=font.name, height=font.size_likert_label,
        wrapWidth=1000 * s,
    )

    mouse = event.Mouse(win=win)
    selected_ui: UiVersion | None = None
    was_pressed = False

    # TextBox2가 키보드 입력을 자체적으로 가로채므로(편집 포커스),
    # 이 화면의 진행은 스페이스바가 아닌 [시작] 버튼 클릭으로 처리한다.
    event.clearEvents()
    while True:
        title.draw()
        id_label.draw()
        id_box.draw()
        ui_label.draw()

        iphone_btn.fillColor = "lightblue" if selected_ui == "iphone" else "white"
        galaxy_btn.fillColor = "lightblue" if selected_ui == "galaxy" else "white"
        iphone_btn.draw()
        iphone_text.draw()
        galaxy_btn.draw()
        galaxy_text.draw()

        start_btn.draw()
        start_text.draw()
        hint.draw()
        error_text.draw()
        win.flip()

        pressed = mouse.getPressed()[0]
        if pressed and not was_pressed:
            pos = mouse.getPos()
            if iphone_btn.contains(pos):
                selected_ui = "iphone"
                error_text.text = ""
            elif galaxy_btn.contains(pos):
                selected_ui = "galaxy"
                error_text.text = ""
            elif start_btn.contains(pos):
                participant_id = id_box.text.strip()
                if not participant_id:
                    error_text.text = "참가자 ID를 입력해주세요 (빈 값으로 시작할 수 없습니다)."
                elif selected_ui is None:
                    error_text.text = "UI 버전을 선택해주세요."
                else:
                    return participant_id, selected_ui
        was_pressed = pressed

        keys = event.getKeys()
        if "escape" in keys:
            confirm_exit(win, config)
            event.clearEvents()

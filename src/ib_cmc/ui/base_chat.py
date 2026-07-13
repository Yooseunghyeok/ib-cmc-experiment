"""iPhone/Galaxy 채팅 화면 표시.

말풍선/헤더를 PsychoPy 도형으로 직접 그리는 대신, `chat_templates/render.py`가
HTML/CSS로 미리 구워둔 PNG(assets/chat/q{item_id}_{ui_version}.png)를 그대로
ImageStim으로 띄운다. 문항이 추가/수정되면 그 스크립트를 다시 돌려야 한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from psychopy import visual

from ..chat_templates.render import chat_image_path
from ..config import AppConfig, ChatFrameConfig
from ..models import Question

Sender = Literal["friend", "me"]


@dataclass(frozen=True)
class ChatMessage:
    sender: Sender
    text: str


class BaseChatRenderer:
    ui_version = "base"

    def __init__(self, win, config: AppConfig):
        self.win = win
        self.config = config
        self.frame: ChatFrameConfig = config.chat_frame

    def build_stims(self, question: Question) -> list:
        frame = self.frame
        image = visual.ImageStim(
            self.win,
            image=chat_image_path(question.item_id, self.ui_version),
            pos=(frame.x, frame.y),
            size=(frame.width, frame.height),
        )
        return [image]

"""iPhone/Galaxy 공통 채팅 말풍선 레이아웃 로직.

상태바, 하단 내비게이션 바는 그리지 않고 헤더(상대 이름)와 말풍선만
config의 chat_frame 영역 안에 위에서 아래로 쌓아 그린다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from psychopy import visual

from ..config import AppConfig, ChatFrameConfig, UiStyleConfig

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
        self.style: UiStyleConfig = config.ui_style[self.ui_version]
        self.frame: ChatFrameConfig = config.chat_frame

    def build_stims(self, messages: list[ChatMessage]) -> list:
        stims: list = []
        frame = self.frame
        style = self.style

        stims.append(
            visual.Rect(
                self.win,
                width=frame.width,
                height=frame.height,
                pos=(frame.x, frame.y),
                fillColor=style.frame_bg,
                lineColor="darkgray",
                lineWidth=1,
            )
        )

        header_y = frame.y + frame.height / 2 - 24
        stims.append(
            visual.TextStim(
                self.win,
                text=style.header_name,
                pos=(frame.x, header_y),
                color="black",
                font=self.config.font.name,
                height=self.config.font.size_chat,
                bold=True,
            )
        )

        cur_y = header_y - 34
        bottom_limit = frame.y - frame.height / 2 + 16
        for msg in messages:
            bubble_stims, used_height = self._build_bubble(msg, cur_y)
            if cur_y - used_height < bottom_limit:
                break
            stims.extend(bubble_stims)
            cur_y -= used_height
        return stims

    def _build_bubble(self, msg: ChatMessage, top_y: float):
        style = self.style
        font = self.config.font
        frame = self.frame
        is_me = msg.sender == "me"

        bubble_color = style.my_bubble_color if is_me else style.friend_bubble_color
        text_color = style.my_text_color if is_me else style.friend_text_color
        max_text_width = frame.width * 0.62
        padding = style.bubble_padding

        text_stim = visual.TextStim(
            self.win,
            text=msg.text,
            font=font.name,
            height=font.size_chat,
            color=text_color,
            wrapWidth=max_text_width,
            alignText="left",
            anchorHoriz="center",
            anchorVert="center",
        )
        text_w, text_h = text_stim.boundingBox
        bubble_w = min(max_text_width, text_w) + padding * 2
        bubble_h = text_h + padding * 2

        side_margin = 16
        if is_me:
            bubble_x = frame.x + frame.width / 2 - bubble_w / 2 - side_margin
        else:
            bubble_x = frame.x - frame.width / 2 + bubble_w / 2 + side_margin

        bubble_y = top_y - bubble_h / 2

        rect = visual.Rect(
            self.win,
            width=bubble_w,
            height=bubble_h,
            pos=(bubble_x, bubble_y),
            fillColor=bubble_color,
            lineColor=None,
        )
        text_stim.pos = (bubble_x, bubble_y)

        used_height = bubble_h + 14
        return [rect, text_stim], used_height

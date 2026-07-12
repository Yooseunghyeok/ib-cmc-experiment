"""config/settings.yaml 로더. UI 크기/위치/색상/폰트 등을 dataclass로 노출한다."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


@dataclass
class WindowConfig:
    size: tuple[int, int]
    fullscreen: bool
    background_color: str


@dataclass
class FontConfig:
    name: str
    size_situation: int
    size_chat: int
    size_interpretation: int
    size_likert_label: int
    size_likert_number: int
    size_instruction: int
    color: str


@dataclass
class ChatFrameConfig:
    x: int
    y: int
    width: int
    height: int


@dataclass
class UiStyleConfig:
    frame_bg: tuple[float, float, float]
    header_name: str
    friend_bubble_color: tuple[float, float, float]
    friend_text_color: str
    my_bubble_color: tuple[float, float, float]
    my_text_color: str
    bubble_corner: int
    bubble_padding: int


@dataclass
class LikertConfig:
    y: int
    spacing: int
    box_size: int


@dataclass
class AppConfig:
    window: WindowConfig
    font: FontConfig
    chat_frame: ChatFrameConfig
    ui_style: dict[str, UiStyleConfig]
    likert: LikertConfig
    data_dir: Path


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    window = WindowConfig(
        size=tuple(raw["window"]["size"]),
        fullscreen=raw["window"]["fullscreen"],
        background_color=raw["window"]["background_color"],
    )
    font = FontConfig(**raw["font"])
    chat_frame = ChatFrameConfig(**raw["chat_frame"])
    ui_style = {
        name: UiStyleConfig(
            frame_bg=tuple(style["frame_bg"]),
            header_name=style["header_name"],
            friend_bubble_color=tuple(style["friend_bubble_color"]),
            friend_text_color=style["friend_text_color"],
            my_bubble_color=tuple(style["my_bubble_color"]),
            my_text_color=style["my_text_color"],
            bubble_corner=style["bubble_corner"],
            bubble_padding=style["bubble_padding"],
        )
        for name, style in raw["ui_style"].items()
    }
    likert = LikertConfig(**raw["likert"])
    data_dir = PROJECT_ROOT / raw["paths"]["data_dir"]

    return AppConfig(
        window=window,
        font=font,
        chat_frame=chat_frame,
        ui_style=ui_style,
        likert=likert,
        data_dir=data_dir,
    )

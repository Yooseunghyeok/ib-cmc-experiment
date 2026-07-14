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
    avatar_color: tuple[float, float, float]
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
class GoogleSheetsConfig:
    enabled: bool = False
    spreadsheet_url: str = ""
    credentials_path: str = "config/google_service_account.json"


@dataclass
class AppConfig:
    window: WindowConfig
    font: FontConfig
    chat_frame: ChatFrameConfig
    ui_style: dict[str, UiStyleConfig]
    likert: LikertConfig
    data_dir: Path
    google_sheets: GoogleSheetsConfig = field(default_factory=GoogleSheetsConfig)
    scale: float = 1.0


# settings.yaml의 모든 px 값은 1280x800 창을 기준으로 잡아둔 것이다. 실제 창은
# 모니터 작업 영역에 맞춰 이보다 훨씬 클 수 있으므로(app.py의 _get_work_area 참고),
# 실제 창 높이에 맞는 배율을 계산해서 폰트/프레임/척도 크기를 한 번에 키운다.
BASELINE_HEIGHT = 800


def apply_scale(config: AppConfig, window_height: int) -> None:
    scale = window_height / BASELINE_HEIGHT
    config.scale = scale

    font = config.font
    font.size_situation = round(font.size_situation * scale)
    font.size_chat = round(font.size_chat * scale)
    font.size_interpretation = round(font.size_interpretation * scale)
    font.size_likert_label = round(font.size_likert_label * scale)
    font.size_likert_number = round(font.size_likert_number * scale)
    font.size_instruction = round(font.size_instruction * scale)

    frame = config.chat_frame
    frame.x = round(frame.x * scale)
    frame.y = round(frame.y * scale)
    frame.width = round(frame.width * scale)
    frame.height = round(frame.height * scale)

    likert = config.likert
    likert.y = round(likert.y * scale)
    likert.spacing = round(likert.spacing * scale)
    likert.box_size = round(likert.box_size * scale)


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
            avatar_color=tuple(style["avatar_color"]),
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
    google_sheets = GoogleSheetsConfig(**raw.get("google_sheets", {}))

    return AppConfig(
        window=window,
        font=font,
        chat_frame=chat_frame,
        ui_style=ui_style,
        likert=likert,
        data_dir=data_dir,
        google_sheets=google_sheets,
    )

from .base_chat import BaseChatRenderer


class GalaxyChatRenderer(BaseChatRenderer):
    """갤럭시 메시지 느낌 스타일. 실제 색상/여백은 config/settings.yaml의
    ui_style.galaxy 값으로 조정한다."""

    ui_version = "galaxy"

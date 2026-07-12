from .base_chat import BaseChatRenderer


class IPhoneChatRenderer(BaseChatRenderer):
    """아이폰 iMessage 느낌 스타일. 실제 색상/여백은 config/settings.yaml의
    ui_style.iphone 값으로 조정한다."""

    ui_version = "iphone"

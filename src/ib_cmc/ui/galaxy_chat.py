from .base_chat import BaseChatRenderer


class GalaxyChatRenderer(BaseChatRenderer):
    """갤럭시 메시지 느낌 스타일. 실제 색상/여백/아이콘은
    chat_templates/render.py가 config/settings.yaml의 ui_style.galaxy 값으로
    미리 렌더링해둔 이미지(assets/chat/)를 그대로 사용한다."""

    ui_version = "galaxy"

"""문항의 상황+채팅 화면을 PsychoPy 도형 대신 HTML/CSS로 그려서 PNG로 구워내는 스크립트.

questions.py에 문항을 추가/수정했거나 config/settings.yaml의 ui_style을 바꿨으면
다시 실행해서 assets/chat/ 아래 이미지를 갱신해야 한다:

    .venv\\Scripts\\python -m ib_cmc.chat_templates.render

PsychoPy(pyglet)의 도형 그리기 API로 말풍선 각도/색상/헤더 아이콘을 일일이 좌표
계산해서 맞추는 대신, 브라우저의 flexbox/border-radius로 그린 뒤 스크린샷을 떠서
그 결과물을 ImageStim으로 띄우는 방식이 훨씬 정확하고 손이 덜 간다.
"""
from __future__ import annotations

from ..config import PROJECT_ROOT, AppConfig, load_config
from ..models import Question
from ..questions import QUESTIONS

ASSETS_DIR = PROJECT_ROOT / "assets" / "chat"


def chat_image_path(item_id: int, ui_version: str) -> str:
    return str(ASSETS_DIR / f"q{item_id}_{ui_version}.png")


def _rgb_css(color) -> str:
    """config의 -1~1 rgb 튜플 또는 색상 이름 문자열을 CSS 색상값으로 바꾼다."""
    if isinstance(color, str):
        return color
    r, g, b = color
    to255 = lambda c: round((c + 1) / 2 * 255)
    return f"rgb({to255(r)}, {to255(g)}, {to255(b)})"


def _ordered_messages(question: Question) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []
    if question.my_message and question.my_message_position == "before":
        messages.append(("me", question.my_message))
    messages.append(("friend", question.friend_message))
    if question.my_message and question.my_message_position == "after":
        messages.append(("me", question.my_message))
    return messages


_IPHONE_HEADER_CSS = """
  .header {
    position: relative;
    display: flex; flex-direction: column; align-items: center;
    padding: 10px 0 8px;
    border-bottom: 1px solid lightgray;
  }
  .back {
    position: absolute; left: 10px; top: 10px;
    font-size: 17px; color: rgb(90, 90, 95);
    display: flex; align-items: center; gap: 2px;
  }
  .avatar { width: 56px; height: 56px; border-radius: 50%; flex-shrink: 0; }
  .namewrap { margin-top: 4px; display: flex; align-items: center; gap: 2px; }
  .name { font-size: 13px; color: rgb(20, 20, 20); font-weight: bold; }
  .chevron { font-size: 12px; color: rgb(150, 150, 150); }
"""

_GALAXY_HEADER_CSS = """
  .header {
    display: flex; align-items: center; gap: 10px;
    height: 62px; padding: 0 12px;
    background: rgb(250, 249, 240);
    border-bottom: 1px solid lightgray;
  }
  .back { font-size: 22px; color: rgb(40, 40, 40); }
  .avatar {
    width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
    background: rgb(150, 195, 245);
    border: 1.5px solid rgb(120, 170, 230);
    display: flex; align-items: center; justify-content: center;
    color: rgb(255, 255, 255); font-size: 13px; font-weight: bold;
  }
  .name { font-weight: bold; font-size: 21px; color: rgb(20,20,20); }
  .spacer { flex: 1; }
  .icon { display: flex; align-items: center; margin-left: 14px; }
"""

_IPHONE_HEADER_BODY = """
  <div class="header">
    <span class="back">&#8249;(뒤로)</span>
    <svg class="avatar" viewBox="0 0 60 60">
      <circle cx="30" cy="30" r="30" fill="rgb(160,160,166)"></circle>
      <circle cx="30" cy="24" r="11" fill="rgb(250,250,251)"></circle>
      <path d="M8 55c2-15 10-21 22-21s20 6 22 21" fill="rgb(250,250,251)"></path>
    </svg>
    <div class="namewrap">
      <span class="name">{name}</span>
      <span class="chevron">&#8250;</span>
    </div>
  </div>
"""

_GALAXY_HEADER_BODY = """
  <div class="header">
    <span class="back">&#8249;</span>
    <div class="avatar">{initial}</div>
    <span class="name">{name}</span>
    <span class="spacer"></span>
    <span class="icon">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgb(40,40,40)" stroke-width="2" stroke-linecap="round">
        <circle cx="11" cy="11" r="7"></circle>
        <line x1="21" y1="21" x2="16.5" y2="16.5"></line>
      </svg>
    </span>
    <span class="icon">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="rgb(40,40,40)">
        <circle cx="12" cy="5" r="2"></circle>
        <circle cx="12" cy="12" r="2"></circle>
        <circle cx="12" cy="19" r="2"></circle>
      </svg>
    </span>
  </div>
"""

# 말풍선 꼬리(tail). 아이폰은 둥근 clip-path 꼬리, 갤럭시는 회전된 사각형(다이아몬드) 꼬리로
# 서로 다르게 그린다 (claude.ai/design에서 다듬은 디자인 그대로).
_IPHONE_BUBBLE_TAIL_CSS = """
  .bubble.friend::after {
    content: "";
    position: absolute;
    left: -11px; bottom: 8px;
    width: 22px; height: 22px;
    background: FRIEND_COLOR;
    border-left: 1px solid gainsboro;
    border-bottom: 1px solid gainsboro;
    border-bottom-left-radius: 8px;
    clip-path: polygon(100% 0, 100% 100%, 0 100%);
  }
  .bubble.me::after {
    content: "";
    position: absolute;
    right: -11px; bottom: 8px;
    width: 22px; height: 22px;
    background: ME_COLOR;
    border-bottom-right-radius: 8px;
    clip-path: polygon(0 0, 100% 100%, 0 100%);
  }
"""

_GALAXY_BUBBLE_TAIL_CSS = """
  .bubble.friend::after {
    content: "";
    position: absolute;
    left: -6px; top: 10px;
    width: 12px; height: 12px;
    background: FRIEND_COLOR;
    border-left: 1px solid gainsboro;
    border-top: 1px solid gainsboro;
    transform: rotate(-45deg);
  }
  .bubble.me::after {
    content: "";
    position: absolute;
    right: -6px; top: 10px;
    width: 12px; height: 12px;
    background: ME_COLOR;
    transform: rotate(45deg);
  }
"""


def build_html(question: Question, ui_version: str, config: AppConfig) -> str:
    """iPhone/Galaxy 헤더는 claude.ai/design에서 직접 다듬은 디자인을 그대로 반영한다
    (아이폰: 큰 실루엣 아바타 + '뒤로' + 세로 정렬 / 갤럭시: 헤더 톤 다르게 + 검색·더보기 아이콘)."""
    style = config.ui_style[ui_version]
    frame = config.chat_frame
    font = config.font

    if ui_version == "iphone":
        header_css = _IPHONE_HEADER_CSS
        header_body = _IPHONE_HEADER_BODY.format(name=style.header_name)
        tail_css = _IPHONE_BUBBLE_TAIL_CSS
    else:
        header_css = _GALAXY_HEADER_CSS
        header_body = _GALAXY_HEADER_BODY.format(
            name=style.header_name, initial=style.header_name[0]
        )
        tail_css = _GALAXY_BUBBLE_TAIL_CSS

    tail_css = tail_css.replace(
        "FRIEND_COLOR", _rgb_css(style.friend_bubble_color)
    ).replace("ME_COLOR", _rgb_css(style.my_bubble_color))

    bubbles = "".join(
        f'<div class="bubble {"me" if sender == "me" else "friend"}">{text}</div>'
        for sender, text in _ordered_messages(question)
    )

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    width: {frame.width}px; height: {frame.height}px;
    background: {_rgb_css(style.frame_bg)};
    font-family: "{font.name}", sans-serif;
    overflow: hidden;
    border: 1px solid darkgray;
  }}
{header_css}
  .body {{
    display: flex; flex-direction: column; gap: 10px;
    padding: 14px;
  }}
  .bubble {{
    position: relative;
    max-width: 62%;
    padding: {style.bubble_padding}px;
    border-radius: {style.bubble_corner}px;
    font-size: {font.size_chat}px;
    line-height: 1.35;
    word-break: keep-all;
  }}
  .bubble.friend {{
    align-self: flex-start;
    background: {_rgb_css(style.friend_bubble_color)};
    color: {_rgb_css(style.friend_text_color)};
    border: 1px solid gainsboro;
  }}
  .bubble.me {{
    align-self: flex-end;
    background: {_rgb_css(style.my_bubble_color)};
    color: {_rgb_css(style.my_text_color)};
  }}
{tail_css}
</style></head>
<body>
{header_body}
  <div class="body">{bubbles}</div>
</body></html>
"""


def render_all() -> None:
    # playwright는 이미지 굽기 스크립트에서만 필요하다. 모듈 최상단에서 import하면
    # base_chat.py(chat_image_path) 경유로 실행용 exe에까지 끌려 들어가서
    # PyInstaller 빌드가 greenlet._greenlet 누락으로 시작 즉시 죽는다.
    from playwright.sync_api import sync_playwright

    config = load_config()
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    # set_content()으로 넣은 페이지는 about:blank 취급이라 file:// 이미지(아바타)를
    # 못 불러온다. 임시 html 파일로 저장해서 goto()로 열어야 로컬 이미지가 뜬다.
    tmp_html = ASSETS_DIR / "_render_tmp.html"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": config.chat_frame.width, "height": config.chat_frame.height},
            device_scale_factor=4,
        )
        for question in QUESTIONS:
            for ui_version in ("iphone", "galaxy"):
                tmp_html.write_text(build_html(question, ui_version, config), encoding="utf-8")
                page.goto(tmp_html.as_uri())
                out_path = chat_image_path(question.item_id, ui_version)
                page.screenshot(path=out_path)
                print("saved", out_path)
        browser.close()
    tmp_html.unlink(missing_ok=True)


if __name__ == "__main__":
    render_all()

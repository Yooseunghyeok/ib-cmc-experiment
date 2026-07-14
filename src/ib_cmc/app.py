"""전체 실험 흐름을 조립하는 상태 머신."""
from __future__ import annotations

import ctypes
import random
import uuid
from datetime import datetime

from psychopy import visual

from .config import PROJECT_ROOT, AppConfig, apply_scale, load_config
from .models import ResponseRecord, SessionState, UiVersion
from .questions import QUESTIONS
from .screens.common import ExperimentAborted
from .screens.complete_screen import run_complete_screen
from .screens.experiment_screen import run_experiment_screen
from .screens.instruction_screen import (
    POST_INSTRUCTION_TEXT,
    PRE_INSTRUCTION_TEXT,
    run_instruction_screen,
)
from .screens.participant_screen import run_participant_screen
from .screens.waiting_screen import run_waiting_screen
from .sequence import build_sequence
from .storage import CompositeStorage, GoogleSheetsStorage, LocalFileStorage, ResultStorage
from .ui.base_chat import BaseChatRenderer
from .ui.galaxy_chat import GalaxyChatRenderer
from .ui.iphone_chat import IPhoneChatRenderer

CHAT_RENDERERS: dict[UiVersion, type[BaseChatRenderer]] = {
    "iphone": IPhoneChatRenderer,
    "galaxy": GalaxyChatRenderer,
}


def _now_iso() -> str:
    return datetime.now().isoformat()


def _build_storage(
    config: AppConfig, participant_id: str, session_id: str
) -> LocalFileStorage | CompositeStorage:
    """로컬 저장은 항상 켜고, settings.yaml의 google_sheets.enabled가 true면
    구글시트 저장을 얹는다. 시트 연결에 실패해도(키 없음/네트워크 등) 실험은
    로컬 저장만으로 계속 진행한다."""
    local = LocalFileStorage(config.data_dir, participant_id, session_id)

    gs = config.google_sheets
    if not gs.enabled:
        return local

    credentials_path = PROJECT_ROOT / gs.credentials_path
    try:
        sheets = GoogleSheetsStorage.from_service_account(gs.spreadsheet_url, credentials_path)
    except Exception as e:
        print(f"[app] 구글시트 연결 실패 — 로컬 저장만 사용합니다: {e}")
        return local
    return CompositeStorage(local, sheets)


def _run_phase(
    win,
    config: AppConfig,
    storage: ResultStorage,
    session: SessionState,
    chat_renderer: BaseChatRenderer,
    phase: str,
    rng: random.Random,
) -> None:
    sequence = build_sequence(QUESTIONS, phase, rng)
    for entry in sequence:
        score, answered_at = run_experiment_screen(
            win, config, chat_renderer, entry.item, entry.interpretation_type
        )
        record = ResponseRecord(
            session_id=session.session_id,
            participant_id=session.participant_id,
            ui_version=session.ui_version,
            phase=entry.phase,
            item_id=entry.item.item_id,
            item_presentation_order=entry.item_presentation_order,
            interpretation_type=entry.interpretation_type,
            interpretation_order=entry.interpretation_order,
            score=score,
            answered_at=answered_at,
            started_at=session.started_at,
            completed_at=None,
            completion_status="in_progress",
        )
        storage.save_response(record)


def _make_process_dpi_aware() -> None:
    """DPI 배율(125%, 150%, 200% 등)이 걸린 모니터에서 Windows가 창을 자동으로
    확대해서 그리는 걸 막는다. 이걸 안 하면 창을 작업 영역 크기로 만들어도
    Windows가 화면 전체 크기로 다시 늘려버려서 타이틀바가 흐릿해지거나 잘려
    실질적으로 전체화면처럼 보이고, 창이 실제 모니터보다 훨씬 작게(또는 크게)
    측정된다."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _get_work_area() -> tuple[int, int, int, int]:
    """Windows 작업표시줄을 제외한 화면 영역을 (left, top, width, height)로 반환한다."""

    class _Rect(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    SPI_GETWORKAREA = 0x0030
    rect = _Rect()
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def create_window(config: AppConfig) -> visual.Window:
    """설정에 맞춰 실험 창을 만들고, 실제 창 높이에 맞는 배율(apply_scale)까지
    적용해서 반환한다. tools/capture_screens.py도 이 함수를 그대로 쓴다."""
    if config.window.fullscreen:
        # 진짜 전체화면(kiosk 모드). 타이틀바/최소화 버튼이 없어져서 대기화면에서
        # "다른 활동 후 복귀" 흐름과는 안 맞으니 특수한 경우가 아니면 권장하지 않음.
        win = visual.Window(
            size=config.window.size,
            fullscr=True,
            color=config.window.background_color,
            units="pix",
            # 주사율 측정 안 함: 측정 중 띄우는 스플래시 문구가 Noto Sans를 요구하는데
            # exe 환경에서 폰트 매니저가 이를 못 찾아 죽는 경우가 있고(간헐적),
            # 이 프로젝트는 주사율 값을 쓰지 않는다.
            checkTiming=False,
        )
    else:
        # 기본값: 일반 창모드로 모니터의 작업 영역(작업표시줄 제외)에 맞춰 크게 띄우되,
        # 작업 영역에 딱 맞추면(특히 위쪽) 타이틀바가 화면 가장자리에 붙어 전체화면처럼
        # 보일 수 있어서 일부러 여백을 남긴다 — 특히 위쪽은 타이틀바가 확실히 보이도록
        # 더 크게 띄운다.
        area_left, area_top, area_width, area_height = _get_work_area()
        side_margin = 40
        top_margin = 60
        win_pos = (area_left + side_margin, area_top + top_margin)
        win_size = (
            area_width - side_margin * 2,
            area_height - top_margin - side_margin,
        )
        win = visual.Window(
            size=win_size,
            pos=win_pos,
            fullscr=False,
            allowGUI=True,
            color=config.window.background_color,
            units="pix",
            checkTiming=False,  # 위 fullscreen 분기의 주석 참고
        )

    # settings.yaml의 px 값들은 1280x800 기준이라, 실제 창이 더 크면(요즘 모니터는
    # 거의 항상 더 크다) 글씨/프레임/척도가 화면에 비해 작아 보인다. 실제 창 높이에
    # 맞춰 한 번에 키운다.
    apply_scale(config, win.size[1])
    return win


def run_experiment(config: AppConfig | None = None) -> None:
    _make_process_dpi_aware()
    config = config or load_config()
    win = create_window(config)

    session: SessionState | None = None
    storage: LocalFileStorage | CompositeStorage | None = None

    try:
        participant_id, ui_version = run_participant_screen(win, config)

        session = SessionState(
            session_id=str(uuid.uuid4()),
            participant_id=participant_id,
            ui_version=ui_version,
            started_at=_now_iso(),
        )
        storage = _build_storage(config, participant_id, session.session_id)
        chat_renderer = CHAT_RENDERERS[ui_version](win, config)

        run_instruction_screen(win, config, PRE_INSTRUCTION_TEXT)
        _run_phase(win, config, storage, session, chat_renderer, "pre", random.Random())

        run_waiting_screen(win, config)

        run_instruction_screen(win, config, POST_INSTRUCTION_TEXT)
        _run_phase(win, config, storage, session, chat_renderer, "post", random.Random())

        session.completed_at = _now_iso()
        session.completion_status = "completed"
        storage.finalize_session(session)

        run_complete_screen(win, config, storage.json_file_path(), storage.csv_path())

    except ExperimentAborted:
        if session is not None and storage is not None:
            session.completed_at = _now_iso()
            session.completion_status = "aborted"
            storage.finalize_session(session)
    finally:
        win.close()

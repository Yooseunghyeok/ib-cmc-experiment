"""전체 실험 흐름을 조립하는 상태 머신."""
from __future__ import annotations

import random
import uuid
from datetime import datetime

from psychopy import visual

from .config import AppConfig, load_config
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
from .storage import LocalFileStorage
from .ui.base_chat import BaseChatRenderer
from .ui.galaxy_chat import GalaxyChatRenderer
from .ui.iphone_chat import IPhoneChatRenderer

CHAT_RENDERERS: dict[UiVersion, type[BaseChatRenderer]] = {
    "iphone": IPhoneChatRenderer,
    "galaxy": GalaxyChatRenderer,
}


def _now_iso() -> str:
    return datetime.now().isoformat()


def _run_phase(
    win,
    config: AppConfig,
    storage: LocalFileStorage,
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


def run_experiment(config: AppConfig | None = None) -> None:
    config = config or load_config()

    win = visual.Window(
        size=config.window.size,
        fullscr=config.window.fullscreen,
        color=config.window.background_color,
        units="pix",
    )

    session: SessionState | None = None
    storage: LocalFileStorage | None = None

    try:
        participant_id, ui_version = run_participant_screen(win, config)

        session = SessionState(
            session_id=str(uuid.uuid4()),
            participant_id=participant_id,
            ui_version=ui_version,
            started_at=_now_iso(),
        )
        storage = LocalFileStorage(config.data_dir, participant_id, session.session_id)
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

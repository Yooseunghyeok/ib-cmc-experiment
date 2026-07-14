"""측정 화면(22문항 × iphone/galaxy × 온건/부정 = 88장)과 부속 화면을
클릭/키 입력 없이 그려서 PNG로 저장하는 검증용 스크립트.

실제 실험과 동일한 창 생성(create_window)·자극 생성(build_* 함수)을 그대로
사용하므로, 여기서 찍힌 스크린샷이 곧 실제 참가자가 보게 될 화면이다.

사용법 (프로젝트 루트에서, 가상환경 활성화 후):
  python tools\\capture_screens.py                        # 전체 88장 + 부속 화면
  python tools\\capture_screens.py --ui iphone            # iPhone 버전만
  python tools\\capture_screens.py --items 1,2,14         # 특정 문항만
  python tools\\capture_screens.py --no-aux               # 측정 화면만

출력: data/preview/q{문항}_{ui}_{benign|negative}.png 및 aux_*.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ib_cmc.app import CHAT_RENDERERS, _make_process_dpi_aware, create_window  # noqa: E402
from ib_cmc.config import load_config  # noqa: E402
from ib_cmc.questions import QUESTIONS  # noqa: E402
from ib_cmc.screens.complete_screen import build_complete_stims  # noqa: E402
from ib_cmc.screens.experiment_screen import build_experiment_stims  # noqa: E402
from ib_cmc.screens.instruction_screen import build_instruction_stim  # noqa: E402
from ib_cmc.screens.participant_screen import build_participant_stims  # noqa: E402
from ib_cmc.screens.waiting_screen import build_waiting_stim  # noqa: E402


def snap(win, stims: list, out_path: Path) -> None:
    """자극들을 한 프레임 그리고 그 화면을 PNG로 저장한다."""
    for stim in stims:
        stim.draw()
    win.flip()
    win.getMovieFrame(buffer="front")
    win.saveMovieFrames(str(out_path))
    print(f"  saved {out_path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--ui", choices=["iphone", "galaxy"], help="한 UI 버전만 캡처")
    parser.add_argument("--items", help="캡처할 문항 번호 (쉼표 구분, 예: 1,2,14)")
    parser.add_argument("--no-aux", action="store_true", help="부속 화면(설명/대기/종료 등)은 캡처하지 않음")
    parser.add_argument("--out", default="data/preview", help="출력 폴더 (기본: data/preview)")
    args = parser.parse_args()

    ui_versions = [args.ui] if args.ui else ["iphone", "galaxy"]
    if args.items:
        wanted = {int(x) for x in args.items.split(",")}
        questions = [q for q in QUESTIONS if q.item_id in wanted]
        missing = wanted - {q.item_id for q in questions}
        if missing:
            parser.error(f"존재하지 않는 문항 번호: {sorted(missing)}")
    else:
        questions = list(QUESTIONS)

    out_dir = PROJECT_ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    _make_process_dpi_aware()
    config = load_config()
    win = create_window(config)

    try:
        for ui_version in ui_versions:
            renderer = CHAT_RENDERERS[ui_version](win, config)
            print(f"[{ui_version}] {len(questions)}문항 × 2해석 캡처 중...")
            for question in questions:
                for interp in ("benign", "negative"):
                    stims, _boxes = build_experiment_stims(win, config, renderer, question, interp)
                    snap(win, stims, out_dir / f"q{question.item_id:02d}_{ui_version}_{interp}.png")

        if not args.no_aux:
            print("[aux] 부속 화면 캡처 중...")
            participant = build_participant_stims(win, config)
            snap(win, list(participant.values()), out_dir / "aux_participant.png")
            snap(win, [build_instruction_stim(win, config, "pre")], out_dir / "aux_instruction_pre.png")
            snap(win, [build_waiting_stim(win, config)], out_dir / "aux_waiting.png")
            snap(win, [build_instruction_stim(win, config, "post")], out_dir / "aux_instruction_post.png")
            example_json = config.data_dir / "<참가자ID>" / "<세션ID>.json"
            example_csv = config.data_dir / "all_responses.csv"
            snap(win, build_complete_stims(win, config, example_json, example_csv), out_dir / "aux_complete.png")
    finally:
        win.close()

    print(f"완료: {out_dir}")


if __name__ == "__main__":
    main()

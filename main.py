import sys
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ib_cmc.app import run_experiment  # noqa: E402

if __name__ == "__main__":
    run_experiment()

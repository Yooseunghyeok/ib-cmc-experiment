# Windows EXE build

Use Python 3.11 from python.org, not MSYS2 Python, and build from a project virtual environment.

```powershell
cd C:\ib-cmc-experiment
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -r requirements-build.txt
python -c "import numpy, scipy, matplotlib, pandas, psychopy; import scipy._lib._ccallback_c; import bidi.bidi; import pandas._libs.pandas_parser; print('imports ok')"
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
python -m PyInstaller --clean --noconfirm IB-CMC.spec
.\dist\IB-CMC\IB-CMC.exe
```

For distribution, zip the entire `dist\IB-CMC` folder. Do not copy only `IB-CMC.exe`; the `_internal` folder is required.
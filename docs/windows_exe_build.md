# Windows EXE build

## 제일 빠른 길

프로젝트 루트에서 `build.bat` 더블클릭. `.venv`가 이미 있으면 그대로 재사용하고
바로 exe를 만든다. 결과는 `dist\IB-CMC`.

## 이 PC(개발기)의 실제 빌드 환경

`C:\icb\.venv` — **Python 3.12.13**. psychopy 2026.2.0 / pyinstaller 6.21.0 /
numpy 2.3.5 / pandas 3.0.3 등이 서로 맞는 조합으로 들어가 있고,
아래 pyglet 버그 패치도 적용되어 있다. 2026-07-26 · 08-22 배포본이 이 환경에서 나왔다.

> `requirements-build.txt`는 numpy==1.26.4, pandas<2.3으로 핀이 박혀 있는데
> 이건 초기(2026-07)에 잡아둔 값이라 지금 `.venv`와 맞지 않는다.
> **이미 있는 `.venv`에 대고 다시 설치하지 말 것** — 다운그레이드로 작동하는 환경이 깨진다.
> 새 환경을 만들 때만 쓰는 파일이다.

## 손으로 빌드할 때

```powershell
cd C:\icb
.\.venv\Scripts\python.exe -c "import numpy, scipy, matplotlib, pandas, psychopy; import scipy._lib._ccallback_c; import bidi.bidi; import pandas._libs.pandas_parser; print('imports ok')"
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm IB-CMC.spec
.\dist\IB-CMC\IB-CMC.exe
```

위 import 확인에서 죽으면 exe에서도 죽는다. 통과하고 나서 빌드할 것.

## 환경을 새로 만들어야 한다면

Python 3.11(python.org 배포본)이 가장 무난하다. MSYS2 파이썬은 쓰지 말 것.
anaconda base에는 절대 설치하지 말 것 — psychopy가 numpy를 강제로 올려서
그 환경의 다른 패키지들이 깨진다 (실제로 겪음).

```powershell
py -3.11 -m venv .venv     # 3.11이 없으면 3.12도 됨 (아래 패치 필수)
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -r requirements-build.txt
```

**Python 3.10 이상이면 pyglet 패치가 필요하다.** psychopy가 고정하는 pyglet 1.4.11이
엄격해진 ctypes 타입 체크와 충돌해서 글자를 그리는 순간 죽는다:

```
ctypes.ArgumentError: argument 5: TypeError: expected LP_c_ubyte instance instead of c_byte_Array_...
```

`.venv\Lib\site-packages\pyglet\font\win32.py`의 `_create_bitmap` 안에서
`c_byte` → `c_ubyte` 한 글자만 고치면 된다. `build.bat`이 새 venv를 만들 때는
이 패치를 자동으로 넣어준다. 자세한 내용은 `README.md` 참고.

## 배포

`dist\IB-CMC` **폴더 통째로** 압축한다. `IB-CMC.exe`만 복사하면 `_internal`이 없어서
실행되지 않는다.

기존 참가자 데이터를 이어가려면 예전 배포본의 `IB-CMC\data` 폴더를 새 폴더에
복사해 넣는다. 구글시트는 시트 URL과 서비스 계정 키가 그대로라 아무것도 안 해도 계속 누적된다.

## 함정: exe에서만 "구글시트 연결 실패"가 날 때 (2026-08-22)

증상은 이랬다. venv에서 `python main.py`로 돌리면 시트에 잘 쓰는데, 같은 코드를
exe로 묶으면 시트에만 아무것도 안 쌓인다. 로컬 저장은 멀쩡해서 눈치채기 어렵다.

원인은 **OpenSSL DLL 짝이 안 맞는 것**이었다. PyInstaller가 `_ssl.pyd`가 필요로 하는
`libssl-3-x64.dll` / `libcrypto-3-x64.dll`을 시스템 PATH에서 찾는데, 이 PC에는 다른
프로그램이 깐 OpenSSL이 먼저 잡혀서 파이썬 것과 다른 파일이 들어갔다. 그러면 exe 안에서
`import _ssl`이 실패하고, 최종 증상은 아래 한 줄로만 나타난다:

```
ImportError: Can't connect to HTTPS URL because the SSL module is not available.
```

`IB-CMC.spec`의 `_openssl_binaries()`가 `sys.base_prefix` 기준으로 **`_ssl.pyd`와 같은
파이썬 설치본의 DLL**을 강제로 넣어서 막아둔다. 빌드 후 아래로 확인할 수 있다:

```powershell
# 두 해시가 같아야 정상
Get-FileHash dist\IB-CMC\_internal\libssl-3-x64.dll
Get-FileHash "$((python -c 'import sys;print(sys.base_prefix)'))\Library\bin\libssl-3-x64.dll"
```

**빌드한 뒤에는 반드시 exe를 실제로 켜서 시트에 행이 쌓이는지 확인할 것.** 참가자 ID를
`zztest` 같은 걸로 한 문항만 응답해보면 된다. 시트 전송 실패는 실험을 막지 않도록
설계되어 있어서(의도된 동작) 조용히 지나간다 — 확인하지 않으면 모른다.

실패 원인은 exe 옆 `IB-CMC-log.txt`에 남는다. 창모드 빌드라 `print`는 아무데도 안 보이므로
이 로그가 유일한 단서다.

@echo off
rem Windows counterpart of the Makefile, for systems without GNU make.
rem Usage (cmd):        make [install | run | data | test | clean]
rem Usage (PowerShell): .\make [install | run | data | test | clean]
setlocal

rem Prefer uv's own Python builds (they include Tk); a python.org install works too.
set "UV_PYTHON_PREFERENCE=managed"
set "MIN_PYTHON=3.13"
set "HINT=install Python %MIN_PYTHON% from https://www.python.org/downloads/ or run: uv python install %MIN_PYTHON%"

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=install"
if /i "%TARGET%"=="clean" goto clean
if /i "%TARGET%"=="install" goto check
if /i "%TARGET%"=="run" goto check
if /i "%TARGET%"=="data" goto check
if /i "%TARGET%"=="test" goto check
echo Unknown target "%TARGET%". Use one of: install, run, data, test, clean.
exit /b 2

rem Fail early with one readable line instead of a long uv/pip traceback.
:check
where uv >nul 2>&1
if errorlevel 1 goto no_uv
set "PYTHON="
for /f "usebackq delims=" %%P in (`uv python find ">=%MIN_PYTHON%" 2^>nul`) do set "PYTHON=%%P"
if not defined PYTHON goto no_python
"%PYTHON%" -c "import tkinter" >nul 2>&1
if errorlevel 1 goto no_tk
goto %TARGET%

:install
uv sync -q --python "%PYTHON%"
if errorlevel 1 exit /b 1
echo Installed. Start the app with: make run
exit /b 0

:run
uv run argus
exit /b %errorlevel%

:data
uv run python scripts/build_data.py
exit /b %errorlevel%

:test
uv run pytest -q
exit /b %errorlevel%

:clean
if exist .venv rmdir /s /q .venv
if exist .pytest_cache rmdir /s /q .pytest_cache
for /d /r %%D in (__pycache__) do if exist "%%D" rmdir /s /q "%%D"
exit /b 0

:no_uv
echo uv is not installed. Install it from https://docs.astral.sh/uv/ and run make install again.
exit /b 2

:no_python
echo Python version is too old. Please %HINT%.
exit /b 2

:no_tk
echo Python at %PYTHON% has no Tk support, which the window needs. Please %HINT%.
exit /b 2

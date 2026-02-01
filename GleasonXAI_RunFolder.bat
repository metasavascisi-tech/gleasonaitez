@echo off
setlocal enabledelayedexpansion

REM ====== CONFIG ======
set "REPO=%~dp0"
set "OUT=%REPO%out"
set "IMG_DIR=%REPO%images"
set "CONV_DIR=%OUT%\converted_rgb"

REM Dataset root (script inside appends \GleasonXAI)
set "DATASET_LOCATION=C:\GleasonXAI_data"

REM ====== PREP ======
if not exist "%OUT%" mkdir "%OUT%"
if not exist "%IMG_DIR%" mkdir "%IMG_DIR%"
if not exist "%CONV_DIR%" mkdir "%CONV_DIR%"

REM ====== ACTIVATE VENV ======
if exist "%REPO%.venv\Scripts\activate.bat" (
  call "%REPO%.venv\Scripts\activate.bat"
) else (
  echo [ERROR] .venv not found at: %REPO%.venv
  pause
  exit /b 1
)

REM ====== ENV VARS ======
set "PYTHONPATH=%REPO%src;%PYTHONPATH%"

echo.
echo ==========================================================
echo  GleasonXAI Windows Runner
echo  Put images into: %IMG_DIR%
echo  Outputs go to:   %OUT%
echo ==========================================================
echo.

REM ====== CONVERT ======
python "%REPO%convert_to_rgb_and_list.py"
if errorlevel 1 (
  echo [ERROR] Conversion step failed.
  pause
  exit /b 1
)

if not exist "%CONV_DIR%\_converted_list.txt" (
  echo [ERROR] Converted list not found: %CONV_DIR%\_converted_list.txt
  pause
  exit /b 1
)

REM ====== RUN MODEL FOR EACH IMAGE ======
for /f "usebackq delims=" %%F in ("%CONV_DIR%\_converted_list.txt") do (
  echo.
  echo [RUN] %%F
  python "%REPO%scripts\run_gleasonXAI.py" --images "%%F" --save_path "%OUT%"
  if errorlevel 1 (
    echo [WARN] Failed on: %%F
  )
)

REM ====== CSV (GP3/4/5) ======
if exist "%REPO%compute_gleason_percentages.py" (
  echo.
  echo [CSV] Computing Gleason percentages from pred_*.png ...
  python "%REPO%compute_gleason_percentages.py" "%OUT%"
) else (
  echo.
  echo [WARN] compute_gleason_percentages.py not found in repo root.
  echo        If you want CSV like Mac, we will add it.
)

echo.
echo [DONE] Opening output folder...
start "" "%OUT%"

echo.
pause
# ==============================
# GleasonXAI Windows Runner (PS1)
# Put images into: .\images
# Outputs: .\out\pred_*.png + .\out\gleason_percentages.csv
# ==============================

$ErrorActionPreference = "Stop"

# --- paths ---
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

$imagesDir = Join-Path $repo "images"
$outDir    = Join-Path $repo "out"
$convDir   = Join-Path $outDir "converted_rgb"

New-Item -ItemType Directory -Force -Path $imagesDir | Out-Null
New-Item -ItemType Directory -Force -Path $outDir    | Out-Null
New-Item -ItemType Directory -Force -Path $convDir   | Out-Null

Write-Host "=========================================================="
Write-Host " GleasonXAI Windows Runner (PS1)"
Write-Host " Put images into: $imagesDir"
Write-Host " Outputs go to:   $outDir"
Write-Host "==========================================================`n"

# --- dataset location (needs to be the ROOT, not ...\GleasonXAI) ---
if (-not $env:DATASET_LOCATION) {
  $env:DATASET_LOCATION = "C:\GleasonXAI_data"
}
Write-Host "[INFO] DATASET_LOCATION = $env:DATASET_LOCATION"

# --- python in venv ---
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  throw "Python venv not found: $python`nActivate/create .venv first."
}

# --- 1) collect input images (jpg/jpeg/png/tif/tiff) ---
$inputs = Get-ChildItem -Path $imagesDir -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Extension -match '^\.(jpg|jpeg|png|tif|tiff)$' }

if (-not $inputs -or $inputs.Count -eq 0) {
  Write-Host "`n[WARN] No images found in $imagesDir"
  Write-Host "       Put images there and run again."
  Read-Host "Press Enter to exit"
  exit 0
}

Write-Host "[INFO] Found $($inputs.Count) image(s). Converting to RGB PNG..."

# --- 2) convert to RGB PNG to avoid 4-channel / alpha errors ---
$converted = @()
foreach ($f in $inputs) {
  $base = [IO.Path]::GetFileNameWithoutExtension($f.Name)
  $dst  = Join-Path $convDir ($base + ".png")

# 4) CSV generation
$csvScript = Join-Path $repo "compute_gleason_percentages.py"

if (Test-Path $csvScript) {
    Write-Host "`n[INFO] Computing CSV from predictions in $outDir"
    & $python $csvScript $outDir
} else {
    Write-Host "[WARN] compute_gleason_percentages.py not found."
}


  if (Test-Path $dst) {
    $converted += $dst
    Write-Host "  OK -> $dst"
  } else {
    Write-Host "  FAIL -> $($f.FullName)"
  }
}

if ($converted.Count -eq 0) {
  Write-Host "[ERROR] No files converted. Exiting."
  Read-Host "Press Enter to exit"
  exit 1
}

# --- 3) run GleasonXAI on each converted file ---
Write-Host "`n[INFO] Running GleasonXAI..."
foreach ($p in $converted) {
  Write-Host "`n[RUN] $p"
  try {
    & $python .\scripts\run_gleasonXAI.py --images "$p" --save_path "$outDir"
  } catch {
    Write-Host "[WARN] Failed on: $p"
    Write-Host $_
  }
}

# --- 4) compute CSV if script exists ---
$csvScript = Join-Path $repo "compute_gleason_percentages.py"
if (Test-Path $csvScript) {
  Write-Host "`n[INFO] Computing CSV from pred_*.png in out..."
  try {
    & $python $csvScript "$outDir"
  } catch {
    Write-Host "[WARN] CSV generation failed."
    Write-Host $_
  }
} else {
  Write-Host "`n[WARN] compute_gleason_percentages.py not found in repo root."
  Write-Host "       (We can add it if you want Mac-like CSV.)"
}

Write-Host "`n[DONE] Opening output folder..."
Start-Process $outDir

Read-Host "Press Enter to close"

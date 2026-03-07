param(
  [switch]$ForceRecreate
)

$ErrorActionPreference = 'Stop'

function Resolve-PythonLauncher {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return @('py', '-3')
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @('python')
  }
  throw 'Python not found. Install Python 3.x or ensure `py` / `python` is on PATH.'
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$venvPath = Join-Path $repoRoot '.venv'
$activatePath = Join-Path $venvPath 'Scripts\Activate.ps1'
$pythonCmd = @(Resolve-PythonLauncher)

if ($ForceRecreate -and (Test-Path $venvPath)) {
  Write-Host "Removing existing .venv..."
  Remove-Item -Recurse -Force $venvPath
}

if (-not (Test-Path $venvPath)) {
  Write-Host "Creating virtual environment at .venv..."
  $pythonExe = $pythonCmd[0]
  $pythonArgs = @()
  if ($pythonCmd.Length -gt 1) {
    $pythonArgs = $pythonCmd[1..($pythonCmd.Length - 1)]
  }
  & $pythonExe @pythonArgs -m venv .venv
}

if (-not (Test-Path $activatePath)) {
  throw "Venv activation script missing at: $activatePath"
}

Write-Host 'Activating virtual environment...'
. $activatePath

Write-Host 'Upgrading pip tooling...'
python -m pip install --upgrade pip setuptools wheel

$reqFile = Join-Path $repoRoot 'requirements.txt'
if (Test-Path $reqFile) {
  Write-Host 'Installing requirements.txt...'
  python -m pip install -r $reqFile
} else {
  Write-Host 'requirements.txt not found; installing minimal dependencies...'
  python -m pip install Django==5.2.11
}

Write-Host ''
Write-Host 'Done.'
Write-Host 'Next:'
Write-Host '  cd paragon_scheduler'
Write-Host '  python manage.py migrate'
Write-Host '  python manage.py runserver'

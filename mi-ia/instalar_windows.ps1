# Instalador de Mi IA para Windows 10/11.
# Uso: clic derecho en este archivo -> "Ejecutar con PowerShell"
#      (o en PowerShell: powershell -ExecutionPolicy Bypass -File .\mi-ia\instalar_windows.ps1)
# Instala con winget: Python, Git, Ollama y Obsidian; descarga los modelos y deja todo listo.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Write-Host "== Mi IA: instalando en $repo ==" -ForegroundColor Cyan

function Instalar($id, $nombre) {
    Write-Host "-> $nombre" -ForegroundColor Yellow
    winget install -e --id $id --accept-package-agreements --accept-source-agreements --silent
}
Instalar "Python.Python.3.12" "Python 3.12"
Instalar "Git.Git" "Git"
Instalar "Ollama.Ollama" "Ollama (el cerebro local)"
Instalar "Obsidian.Obsidian" "Obsidian (la memoria)"

# Refrescar PATH en esta ventana
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "-> Descargando modelos de Ollama (unos 5 GB, tarda un rato)" -ForegroundColor Yellow
ollama pull qwen3:8b
ollama pull nomic-embed-text

Write-Host "-> Librerías para la red neuronal propia" -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install torch regex

# Instrucciones globales para Claude Code: que guarde lecciones en esta bóveda desde cualquier proyecto
$claudeDir = Join-Path $env:USERPROFILE ".claude"
New-Item -ItemType Directory -Force -Path $claudeDir | Out-Null
$global = Join-Path $claudeDir "CLAUDE.md"
$bloque = (Get-Content (Join-Path $PSScriptRoot "claude_global_CLAUDE.md") -Raw).Replace("{{BOVEDA}}", (Join-Path $repo "vault"))
if (-not (Test-Path $global) -or -not (Select-String -Path $global -Pattern "MI-IA-MEMORIA" -Quiet)) {
    Add-Content -Path $global -Value "`n$bloque"
    Write-Host "-> Añadidas las instrucciones de memoria a $global" -ForegroundColor Yellow
}

# Acceso directo en el escritorio
$atajo = Join-Path ([Environment]::GetFolderPath("Desktop")) "Mi IA.lnk"
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($atajo)
$s.TargetPath = Join-Path $PSScriptRoot "MiIA.bat"
$s.WorkingDirectory = $PSScriptRoot
$s.Save()

Write-Host ""
Write-Host "LISTO." -ForegroundColor Green
Write-Host " - Doble clic en 'Mi IA' en el escritorio -> se abre en el navegador."
Write-Host " - En Obsidian: 'Open folder as vault' -> $repo\vault"

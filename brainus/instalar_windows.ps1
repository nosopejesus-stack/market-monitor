# Instalador de BRAINUS para Windows 10/11.
# Uso: clic derecho en este archivo -> "Ejecutar con PowerShell"
#      (o en PowerShell: powershell -ExecutionPolicy Bypass -File .\brainus\instalar_windows.ps1)
# Instala Python, Git, Ollama y Obsidian; elige el cerebro más potente que aguanta tu PC; deja el acceso directo.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Write-Host "== BRAINUS: instalando en $repo ==" -ForegroundColor Cyan

function Instalar($id, $nombre) {
    Write-Host "-> $nombre" -ForegroundColor Yellow
    winget install -e --id $id --accept-package-agreements --accept-source-agreements --silent
}
Instalar "Python.Python.3.12" "Python 3.12"
Instalar "Git.Git" "Git"
Instalar "Ollama.Ollama" "Ollama (motor para cerebros abiertos)"
Instalar "Obsidian.Obsidian" "Obsidian (la memoria)"
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

# ---- Elegir el cerebro más potente que cabe en este PC ----
$ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
$vramGB = 0
try {
    $smi = & nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>$null
    if ($smi) { $vramGB = [math]::Round(([int]($smi | Select-Object -First 1)) / 1024) }
} catch {}
if     ($vramGB -ge 22) { $modelo = "qwen3:32b" }        # GPU de 24 GB: el más listo
elseif ($vramGB -ge 14) { $modelo = "qwen3:14b" }        # GPU de 16 GB
elseif ($ramGB  -ge 30) { $modelo = "qwen3:30b-a3b" }    # MoE: listo y rápido incluso en CPU con 32 GB
elseif ($vramGB -ge 7 -or $ramGB -ge 14) { $modelo = "qwen3:8b" }
else                    { $modelo = "qwen3:4b" }         # PCs modestos
Write-Host "-> Tu PC: $ramGB GB de RAM, $vramGB GB de VRAM NVIDIA. Cerebro elegido: $modelo" -ForegroundColor Green

Write-Host "-> Descargando el cerebro y el modelo de búsqueda (puede tardar)" -ForegroundColor Yellow
ollama pull $modelo
ollama pull nomic-embed-text

$config = @{ modelo = $modelo; embed = "nomic-embed-text"; motor = "ollama"; boveda = (Join-Path $repo "vault") }
$config | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $PSScriptRoot "config.json")

# ---- Red neuronal propia (PyTorch). Con GPU NVIDIA se instala la versión CUDA ----
Write-Host "-> Librerías de la red neuronal propia" -ForegroundColor Yellow
python -m pip install --upgrade pip
if ($vramGB -gt 0) { python -m pip install torch --index-url https://download.pytorch.org/whl/cu124 }
else               { python -m pip install torch }
python -m pip install numpy regex pytest pyarrow

# ---- Claude Code guarda lo aprendido en tu bóveda, desde cualquier proyecto ----
$claudeDir = Join-Path $env:USERPROFILE ".claude"
New-Item -ItemType Directory -Force -Path $claudeDir | Out-Null
$global = Join-Path $claudeDir "CLAUDE.md"
$bloque = (Get-Content (Join-Path $PSScriptRoot "claude_global_CLAUDE.md") -Raw).Replace("{{BOVEDA}}", (Join-Path $repo "vault"))
if (-not (Test-Path $global) -or -not (Select-String -Path $global -Pattern "BRAINUS-MEMORIA" -Quiet)) {
    Add-Content -Path $global -Value "`n$bloque"
    Write-Host "-> Instrucciones de memoria añadidas a $global" -ForegroundColor Yellow
}

# ---- Acceso directo en el escritorio ----
$atajo = Join-Path ([Environment]::GetFolderPath("Desktop")) "Brainus.lnk"
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($atajo)
$s.TargetPath = Join-Path $PSScriptRoot "Brainus.bat"
$s.WorkingDirectory = $PSScriptRoot
$s.Save()

Write-Host ""
Write-Host "LISTO. Brainus está instalado." -ForegroundColor Green
Write-Host " - Doble clic en 'Brainus' en el escritorio: se abre en el navegador."
Write-Host " - Obsidian: 'Open folder as vault' -> $repo\vault"
Write-Host " - Comprobar la red propia: python -m pytest brainus\red_neuronal\test_red.py"

$ErrorActionPreference = "Stop"

# ===== 1) 基础路径 =====
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvDir     = Join-Path $projectRoot ".venv"
$litellmExe  = Join-Path $venvDir "Scripts\litellm.exe"
$configPath  = Join-Path $projectRoot "tools\litellm_config.yaml"
$logDir      = Join-Path $projectRoot "tools\logs"

# ===== 2) 环境变量检查 =====
if (-not $env:YUNWU_API_BASE) {
    throw "YUNWU_API_BASE 未设置。请先设置为 https://yunwu.ai/v1"
}

if (-not $env:YUNWU_API_KEY) {
    throw "YUNWU_API_KEY 未设置。请先设置为你的优质gemini分组 token"
}

# ===== 3) 文件检查 =====
if (-not (Test-Path $litellmExe)) {
    throw "未找到 LiteLLM 可执行文件：$litellmExe"
}

if (-not (Test-Path $configPath)) {
    throw "未找到配置文件：$configPath"
}

# ===== 4) 日志目录 =====
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile   = Join-Path $logDir "litellm-$timestamp.log"

# ===== 5) 启动信息 =====
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " LiteLLM Proxy Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project Root    : $projectRoot"
Write-Host "LiteLLM EXE     : $litellmExe"
Write-Host "Config File     : $configPath"
Write-Host "YUNWU_API_BASE  : $env:YUNWU_API_BASE"
Write-Host "Proxy URL       : http://127.0.0.1:4000"
Write-Host "Debug Mode      : --detailed_debug"
Write-Host "Log File        : $logFile"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ===== 6) 用 Transcript 记录终端输出 =====
$oldErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"

try {
    Start-Transcript -Path $logFile -Append | Out-Null
} catch {
    Write-Warning "无法启动 Transcript，日志将只显示在终端。"
}

$exitCode = $null

try {
    & $litellmExe --config $configPath --detailed_debug
    $exitCode = $LASTEXITCODE
}
finally {
    try {
        Stop-Transcript | Out-Null
    } catch {
    }

    $ErrorActionPreference = $oldErrorActionPreference

    Write-Host ""
    Write-Host "LiteLLM 已退出。" -ForegroundColor Yellow
    if ($null -ne $exitCode) {
        Write-Host "退出码: $exitCode" -ForegroundColor Yellow
    }
    Write-Host "日志文件: $logFile" -ForegroundColor Yellow
}
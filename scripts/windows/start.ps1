<#
  图书漂流管理系统：Windows 一键启动（由仓库根目录的 start.bat 调用）
  打开两个窗口分别运行后端和前端，就绪后自动打开浏览器。关闭这两个窗口即停止系统。
  参数：
    -BackendPort 8001  后端换端口（8000 被系统保留或占用时使用）
    -Lan               允许同一局域网的其他电脑访问前端
  只使用 Windows 自带 PowerShell 5.1 支持的语法。
#>
param(
    [int]$BackendPort = 8000,
    [switch]$Lan
)

# PowerShell 5.1 的 Invoke-WebRequest 显示进度条时非常慢
$ProgressPreference = 'SilentlyContinue'

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$venvPython = Join-Path $backend '.venv\Scripts\python.exe'
$frontendPort = 5173
$frontendUrl = "http://localhost:$frontendPort"
$backendUrl = "http://127.0.0.1:$BackendPort/api/categories"

function Quote([string]$text) {
    return "'" + $text.Replace("'", "''") + "'"
}

# 用 -EncodedCommand 传命令，路径里有空格、引号或中文都不会被拆错
function Start-ConsoleWindow([string]$title, [string]$command) {
    $full = "`$Host.UI.RawUI.WindowTitle = $(Quote $title); $command"
    $encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($full))
    Start-Process powershell -ArgumentList @('-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', $encoded)
}

function Test-PortInUse([int]$port) {
    return $null -ne (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Url([string]$url, [int]$seconds) {
    for ($i = 0; $i -lt $seconds; $i++) {
        try {
            Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null
            return $true
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

if (-not (Test-Path $venvPython) -or -not (Test-Path (Join-Path $frontend 'node_modules'))) {
    Write-Host '还没有安装依赖，请先双击运行 setup.bat。' -ForegroundColor Red
    exit 1
}

foreach ($port in @($BackendPort, $frontendPort)) {
    if (Test-PortInUse $port) {
        Write-Host "端口 $port 已被占用。如果系统已经在运行，请先关闭之前打开的后端、前端窗口；" -ForegroundColor Red
        Write-Host "如果是其他程序占用了后端端口，可以在命令行运行：start.bat -BackendPort 8001" -ForegroundColor Red
        exit 1
    }
}

Write-Host '正在启动后端和前端，请不要关闭弹出的两个窗口……' -ForegroundColor Green

Start-ConsoleWindow '图书漂流 - 后端' (
    "Set-Location -LiteralPath $(Quote $backend); " +
    "& $(Quote $venvPython) -m uvicorn app.main:app --port $BackendPort"
)

$viteHost = ''
if ($Lan) { $viteHost = ' -- --host' }
Start-ConsoleWindow '图书漂流 - 前端' (
    "`$env:VITE_BACKEND = 'http://127.0.0.1:$BackendPort'; " +
    "Set-Location -LiteralPath $(Quote $frontend); " +
    "npm.cmd run dev$viteHost"
)

if (-not (Wait-Url $backendUrl 60)) {
    Write-Host '后端 60 秒内没有启动成功，请查看"图书漂流 - 后端"窗口里的报错。' -ForegroundColor Red
    exit 1
}
if (-not (Wait-Url $frontendUrl 60)) {
    Write-Host '前端 60 秒内没有启动成功，请查看"图书漂流 - 前端"窗口里的报错。' -ForegroundColor Red
    exit 1
}

Start-Process $frontendUrl
Write-Host ""
Write-Host "已启动：$frontendUrl（管理员账号 admin / admin123）" -ForegroundColor Green
Write-Host "接口文档：http://127.0.0.1:$BackendPort/docs"
if ($Lan) {
    Write-Host '局域网访问地址见"图书漂流 - 前端"窗口里的 Network 一行，并在 Windows 防火墙中允许 Node.js 访问网络。'
}
Write-Host '停止系统：关闭"图书漂流 - 后端"和"图书漂流 - 前端"两个窗口。'

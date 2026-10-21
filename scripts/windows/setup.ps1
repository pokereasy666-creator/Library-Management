<#
  图书漂流管理系统：Windows 一键安装（由仓库根目录的 setup.bat 调用）
  1. 检查 Python 3.13 / 3.14（64 位）和 Node.js
  2. 创建后端虚拟环境并安装依赖，首次运行时生成 backend\.env（随机 JWT 密钥）
  3. 安装前端依赖
  参数：-Mirror  使用国内镜像源（pip 清华源、npm npmmirror）
  只使用 Windows 自带 PowerShell 5.1 支持的语法。
#>
param(
    [switch]$Mirror
)

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$venvPython = Join-Path $backend '.venv\Scripts\python.exe'

# 打印 "3.13" 这样的版本号；只有 64 位的 3.13 / 3.14 返回 0（3.15 缺少 Windows 预编译依赖）
$pythonCheck = "import sys, struct; v = sys.version_info[:2]; print('%d.%d' % v); " +
    "sys.exit(0 if v in ((3, 13), (3, 14)) and struct.calcsize('P') == 8 else 1)"

function Write-Step([string]$text) {
    Write-Host ""
    Write-Host "==> $text" -ForegroundColor Cyan
}

function Stop-WithError([string]$text) {
    Write-Host ""
    Write-Host "[失败] $text" -ForegroundColor Red
    exit 1
}

function Assert-Success([string]$what) {
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError "$what 失败（退出码 $LASTEXITCODE），请查看上面的输出。"
    }
}

function Find-Python {
    $candidates = @(
        @{ Exe = 'py'; Args = @('-3.13') },
        @{ Exe = 'py'; Args = @('-3.14') },
        @{ Exe = 'python'; Args = @() }
    )
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.Exe -ErrorAction SilentlyContinue)) { continue }
        $cArgs = $c.Args
        $version = & $c.Exe @cArgs -c $pythonCheck 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Exe = $c.Exe; Args = $c.Args; Version = "$version".Trim() }
        }
    }
    return $null
}

function New-EnvFile([string]$templatePath, [string]$targetPath) {
    $template = [System.IO.File]::ReadAllText($templatePath, [System.Text.Encoding]::UTF8)
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    $secret = -join ($bytes | ForEach-Object { $_.ToString('x2') })
    $content = $template -replace '(?m)^JWT_SECRET=[^\r\n]*', "JWT_SECRET=$secret"
    # 写成不带 BOM 的 UTF-8；PowerShell 5.1 的 Set-Content / > 会写成 BOM 或 UTF-16
    [System.IO.File]::WriteAllText($targetPath, $content, (New-Object System.Text.UTF8Encoding($false)))
}

Write-Host "图书漂流管理系统 - 安装依赖" -ForegroundColor Green
Write-Host "项目目录：$root"

Write-Step '检查 Python'
$python = Find-Python
if ($null -eq $python) {
    Stop-WithError ("没有找到 64 位的 Python 3.13 或 3.14。请到 https://www.python.org/downloads/windows/ " +
        "下载 Python 3.13 的 Windows installer (64-bit)，安装时勾选 Add python.exe to PATH。" +
        "不要安装 3.15：部分依赖还没有它的 Windows 安装包。")
}
Write-Host "使用 Python $($python.Version)（$($python.Exe) $($python.Args -join ' ')）"

Write-Step '检查 Node.js'
if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    Stop-WithError '没有找到 Node.js。请到 https://nodejs.org/ 下载 22 LTS 版本的 Windows 安装包，装好后重新打开本窗口。'
}
$nodeVersion = "$(& node -v)".Trim().TrimStart('v')
$parts = $nodeVersion.Split('.')
$major = [int]$parts[0]
$minor = [int]$parts[1]
$nodeOk = ($major -gt 22) -or ($major -eq 22 -and $minor -ge 12) -or ($major -eq 20 -and $minor -ge 19)
if (-not $nodeOk) {
    Stop-WithError "当前 Node.js 版本是 $nodeVersion，前端需要 22.12 及以上（或 20.19 及以上）。请安装 Node.js 22 LTS。"
}
Write-Host "使用 Node.js $nodeVersion"

Write-Step '创建后端虚拟环境 backend\.venv'
if (Test-Path $venvPython) {
    & $venvPython -c $pythonCheck *> $null
    if ($LASTEXITCODE -ne 0) {
        Stop-WithError '已有的 backend\.venv 不是用 64 位 Python 3.13 / 3.14 创建的，请删除 backend\.venv 文件夹后重新运行。'
    }
    Write-Host '虚拟环境已存在，跳过创建'
} else {
    $pyArgs = $python.Args
    & $python.Exe @pyArgs -m venv (Join-Path $backend '.venv')
    Assert-Success '创建虚拟环境'
}

Write-Step '安装后端依赖'
$pipArgs = @('-m', 'pip', 'install', '-r', (Join-Path $backend 'requirements-dev.txt'))
if ($Mirror) { $pipArgs += @('-i', 'https://pypi.tuna.tsinghua.edu.cn/simple') }
& $venvPython @pipArgs
Assert-Success '安装后端依赖'

Write-Step '生成后端配置 backend\.env'
$envFile = Join-Path $backend '.env'
if (Test-Path $envFile) {
    Write-Host '已存在 backend\.env，保留原有配置'
} else {
    try {
        New-EnvFile (Join-Path $backend '.env.example') $envFile
    } catch {
        Stop-WithError "生成 backend\.env 失败：$($_.Exception.Message)"
    }
    Write-Host '已从 .env.example 生成，并写入随机的 JWT_SECRET'
}

Write-Step '安装前端依赖'
$npmArgs = @('ci')
if ($Mirror) { $npmArgs += '--registry=https://registry.npmmirror.com' }
Push-Location $frontend
try {
    & npm.cmd @npmArgs
} finally {
    Pop-Location
}
Assert-Success '安装前端依赖'

Write-Host ""
Write-Host "安装完成！双击 start.bat 启动系统。" -ForegroundColor Green
Write-Host "管理员账号：admin / admin123。想换初始密码，请在第一次启动前修改 backend\.env 里的 ADMIN_PASSWORD。"

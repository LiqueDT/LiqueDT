$ErrorActionPreference = "Stop"
$AppDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$Port = 8765
Set-Location -LiteralPath $AppDirectory

$Python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
}

if ($Python) {
    Start-Process "http://127.0.0.1:$Port"
    & $Python .\server.py --host 127.0.0.1 --port $Port
} else {
    Write-Host "Python 3 was not found. Opening the offline shell; live news and calendar need server.py." -ForegroundColor Yellow
    Start-Process (Join-Path $AppDirectory "index.html")
}

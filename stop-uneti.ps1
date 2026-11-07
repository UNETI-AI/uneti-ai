# Dung UNETI AI - giet theo DUNG python cua venv nay (moi tien trinh cha/con), khong dua vao port/tieu de.
$killed = $false
$stopped = @()
# Chi tat server cua CHINH thu muc nay. Tren may co the con mot ban khac, hoac chuong trinh khac cung ten
# server\main.py, hoac chuong trinh khac dang giu cong: nhung thu do khong phai viec cua file nay.
# LUU Y: python cua venv chi la LAUNCHER - no re-exec Python goc lam tien trinh CON (con nay moi giu port),
# nen exe cua con la Python goc. "Cua thu muc nay" = chinh no hoac tien trinh cha chay tu .venv o day.
$venv = (Join-Path $PSScriptRoot '.venv') + '\'
$pythons = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue)
function Find-Python($id) { $pythons | Where-Object { $_.ProcessId -eq $id } | Select-Object -First 1 }
function Test-FromVenv($p) { $p -and "$($p.ExecutablePath)".StartsWith($venv, [StringComparison]::OrdinalIgnoreCase) }
function Stop-Server($id, $note) {
  Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
  Write-Host "  - Da tat python PID $id$note"
}
foreach ($p in $pythons) {
  if ("$($p.CommandLine)" -notmatch '(^|[\\/\s"])main\.py|uvicorn.+main:app') { continue }
  if ((Test-FromVenv $p) -or (Test-FromVenv (Find-Python $p.ParentProcessId))) {
    Stop-Server $p.ProcessId ''
    $stopped += $p.ProcessId
    $killed = $true
  }
}
# Cong: dung thu tu cua server - bien moi truong, roi .env canh file nay, roi 7777.
$port = $env:UNETI_PORT
if (-not $port) {
  $m = [regex]::Matches("$(Get-Content -LiteralPath (Join-Path $PSScriptRoot '.env') -Raw -ErrorAction SilentlyContinue)", '(?m)^\s*(?:export\s+)?UNETI_PORT\s*=\s*["'']?(\d+)')
  $port = if ($m.Count) { $m[$m.Count - 1].Groups[1].Value } else { '7777' }
}
# Phong ho: con ai giu cong. Server cua ban nay ma launcher da chet (khong con tien trinh cha) thi tat;
# con lai la chuong trinh khac: chi bao, KHONG tat.
Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
  $id = $_.OwningProcess
  if ($stopped -contains $id) { return }
  $p = Find-Python $id
  if ($p -and "$($p.CommandLine)" -match 'server[\\/]main\.py' -and -not (Get-Process -Id $p.ParentProcessId -ErrorAction SilentlyContinue)) {
    Stop-Server $id " (chu cong $port)"
    $killed = $true
  } else {
    Write-Host "  (Cong $port dang thuoc chuong trinh khac, PID $id. Khong tat chuong trinh do.)"
  }
}
if (-not $killed) { Write-Host '  (Khong thay server nao dang chay)' }
exit 0

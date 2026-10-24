param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $project

$python = Join-Path $project ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "No se encontró .venv\Scripts\python.exe. Creá el entorno virtual e instalá requirements-dev.txt."
}

$version = & $python -c "from app.version import APP_VERSION; print(APP_VERSION)"
$version = "$version".Trim()
if (-not $version) {
    throw "No se pudo leer APP_VERSION."
}
Write-Host "ALKIMIA POS v$version"

if (-not (Test-Path -LiteralPath ".env")) {
    Write-Warning "No existe .env; la app compilada no podrá conectarse a Supabase."
}

foreach ($path in @("build", "dist\ALKIMIA")) {
    if (-not (Test-Path -LiteralPath $path)) {
        continue
    }
    $removed = $false
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction Stop
            $removed = $true
            break
        } catch {
            Start-Sleep -Milliseconds 700
        }
    }
    if (-not $removed) {
        throw "No se pudo limpiar $path. Cerrá ALKIMIA y pausá OneDrive/antivirus, luego reintentá."
    }
}

& $python -m PyInstaller --noconfirm --clean alkimia.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller falló."
}

$exe = Join-Path $project "dist\ALKIMIA\ALKIMIA.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    throw "No se generó dist\ALKIMIA\ALKIMIA.exe."
}

if ($SkipInstaller) {
    Write-Host "Build listo: $exe"
    return
}

$isccCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates |
    Where-Object { $_ -and (Test-Path -LiteralPath $_) } |
    Select-Object -First 1

if (-not $iscc) {
    Write-Warning "Inno Setup 6 no está instalado. Descargalo desde https://jrsoftware.org/isdl.php"
    Write-Host "El ejecutable quedó en: $exe"
    return
}

& $iscc "/DAppVersion=$version" "installer\alkimia.iss"
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup falló."
}

$installer = Join-Path $project ("dist\installer\ALKIMIA-Setup-{0}.exe" -f $version)
if (-not (Test-Path -LiteralPath $installer)) {
    throw "No se generó el instalador."
}

$hash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
$size = [math]::Round((Get-Item -LiteralPath $installer).Length / 1MB, 1)
$releasedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$release = [ordered]@{
    version      = $version
    file         = (Split-Path -Leaf $installer)
    size_mb      = $size
    sha256       = $hash
    created_at   = $releasedAt
    download_url = ""
}
$releasePath = Join-Path $project "dist\installer\release.json"
$release | ConvertTo-Json | Set-Content -LiteralPath $releasePath -Encoding UTF8

Write-Host ""
Write-Host "Instalador generado: $installer"
Write-Host "Tamaño: $size MB"
Write-Host "SHA-256: $hash"
Write-Host "Metadatos: $releasePath"
Write-Host ""
Write-Host "Para publicar la actualización:"
Write-Host "1. Subí el instalador a Supabase Storage o GitHub Releases."
Write-Host "2. Ejecutá supabase/updates.sql una vez en Supabase."
Write-Host "3. Insertá en app_releases: version, download_url, sha256 y notes."

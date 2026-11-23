param(
    [ValidateSet('pl','en')][string]$Language = 'pl',
    [switch]$PrepareOnly,
    [switch]$CheckOnly,
    [switch]$InstallLocalPython,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$AppArgs
)
$ErrorActionPreference = 'Stop'
function Text([string]$pl, [string]$en) { if ($Language -eq 'en') { return $en }; return $pl }
# An explicit startup choice overrides the remembered UI language for this run.
if ($PSBoundParameters.ContainsKey('Language')) { $env:QNMR_LAB_LANGUAGE = $Language }
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$environmentPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$requirementsPath = Join-Path $projectRoot 'requirements-lock.txt'
$stampPath = Join-Path $projectRoot '.venv\qnmr-environment.sha256'
$lockPath = Join-Path $projectRoot '.bootstrap.lock'
$shaAlgorithm = [System.Security.Cryptography.SHA256]::Create()
try { $environmentHash = ([System.BitConverter]::ToString($shaAlgorithm.ComputeHash([System.IO.File]::ReadAllBytes($requirementsPath)))).Replace('-', '') }
finally { $shaAlgorithm.Dispose() }

function Test-CompatiblePython([string]$candidate) {
    if (-not $candidate -or -not (Test-Path -LiteralPath $candidate)) { return $false }
    & $candidate -c "import sys,struct,platform;sys.exit(0 if sys.version_info[:2]==(3,12) and struct.calcsize('P')==8 and platform.machine().lower() in ('amd64','x86_64') else 1)" 2>$null
    return $LASTEXITCODE -eq 0
}

function Find-CompatiblePython {
    $localRuntime = Join-Path $projectRoot '.runtime\Python312\python.exe'
    if (Test-CompatiblePython $localRuntime) { return $localRuntime }
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        $candidate = & $launcher.Source -3.12 -c 'import sys;print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0 -and (Test-CompatiblePython "$candidate")) { return "$candidate" }
    }
    $command = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($command -and (Test-CompatiblePython $command.Source)) { return $command.Source }
    $candidate = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    if (Test-CompatiblePython $candidate) { return $candidate }
    return $null
}

function Install-LocalRuntime {
    $runtimeRoot = Join-Path $projectRoot '.runtime'
    New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
    $installer = Join-Path $runtimeRoot 'python-3.12.10-amd64.exe'
    Write-Host (Text 'Pobieranie oficjalnego Pythona 3.12.10 do folderu aplikacji...' 'Downloading official Python 3.12.10 into this project only...')
    Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile $installer -UseBasicParsing
    $signature = Get-AuthenticodeSignature -LiteralPath $installer
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
        throw (Text 'Nie można zweryfikować podpisu instalatora Pythona. Instalator nie został uruchomiony.' 'Official Python installer signature could not be verified. No installer was run.')
    }
    $target = Join-Path $runtimeRoot 'Python312'
    $arguments = '/quiet InstallAllUsers=0 PrependPath=0 Include_launcher=0 Include_test=0 Include_doc=0 Shortcuts=0 AssociateFiles=0 Include_pip=1 TargetDir="' + $target + '"'
    $process = Start-Process -FilePath $installer -ArgumentList $arguments -PassThru -Wait -WindowStyle Hidden
    if ($process.ExitCode -ne 0) { throw (Text "Instalacja Pythona zakończona kodem $($process.ExitCode)." "Local Python installation failed with exit code $($process.ExitCode).") }
}

$bootstrapLock = $null
try {
    Set-Location -LiteralPath $projectRoot
    try { $bootstrapLock = [System.IO.File]::Open($lockPath, 'OpenOrCreate', 'ReadWrite', 'None') }
    catch { throw (Text 'Trwa inne przygotowanie środowiska qNMR Lab. Poczekaj na zakończenie i spróbuj ponownie.' 'Another qNMR Lab environment preparation is running. Wait for it to finish and try again.') }
    if (-not (Test-CompatiblePython $environmentPython)) {
        if ($CheckOnly) { throw (Text 'Środowisko qNMR Lab nie jest jeszcze przygotowane.' 'A compatible qNMR environment has not been prepared.') }
        if (Test-Path -LiteralPath (Join-Path $projectRoot '.venv')) {
            throw (Text 'Folder .venv jest niezgodny lub uszkodzony. Zmień jego nazwę i uruchom ponownie. Folder nie został usunięty.' 'The existing .venv is incompatible or damaged. Rename that project-local folder and restart. It has not been deleted.')
        }
        $hostPython = Find-CompatiblePython
        if (-not $hostPython -and $InstallLocalPython) { Install-LocalRuntime; $hostPython = Find-CompatiblePython }
        if (-not $hostPython) {
            throw (Text 'Wymagany Python 3.12 x64. Pobierz z https://www.python.org/downloads/windows/ lub uruchom Start_qNMR_Lab.bat -InstallLocalPython, aby zainstalować podpisaną kopię lokalną. Nie zmieniono Pythona systemowego.' 'Python 3.12 x64 is required. Install from https://www.python.org/downloads/windows/ or explicitly run Start_qNMR_Lab.bat -InstallLocalPython for a signature-verified local runtime. No system Python was changed.')
        }
        Write-Host (Text 'Tworzenie środowiska Pythona w folderze aplikacji...' 'Creating a project-local Python environment...')
        & $hostPython -m venv (Join-Path $projectRoot '.venv')
        if ($LASTEXITCODE -ne 0) { throw (Text 'Nie można utworzyć .venv. Sprawdź wolne miejsce i uprawnienia zapisu.' 'Could not create .venv. Check free space and write permissions.') }
    }
    $existingStamp = if (Test-Path -LiteralPath $stampPath) { (Get-Content -LiteralPath $stampPath -Raw).Trim() } else { '' }
    if ($existingStamp -ne $environmentHash) {
        if ($CheckOnly) { throw (Text 'Wymagana weryfikacja bibliotek. Uruchom aplikację normalnie.' 'Environment dependency verification is required. Run the launcher normally.') }
        Write-Host (Text 'Instalacja bibliotek (pierwsze uruchomienie lub zmiana zależności)...' 'Installing pinned dependencies (first launch, or changed dependency lock)...')
        & $environmentPython -m pip install --disable-pip-version-check --only-binary=:all: --timeout 25 --retries 1 -r $requirementsPath
        if ($LASTEXITCODE -ne 0) { throw (Text 'Instalacja bibliotek nie powiodła się. Sprawdź Internet/proxy i uruchom ponownie. Istniejące biblioteki zachowano.' 'Dependency installation failed. Check network/proxy settings. Existing packages were retained; launch again when connectivity is restored.') }
        & $environmentPython (Join-Path $PSScriptRoot 'verify_environment.py') --language $Language
        if ($LASTEXITCODE -ne 0) { throw (Text 'Weryfikacja bibliotek nie powiodła się. Szczegóły powyżej.' 'Dependency verification failed. See details above.') }
        Set-Content -LiteralPath $stampPath -Value $environmentHash -Encoding ascii
    }
    # Lightweight imports on every launch detect damage without reinstalling.
    & $environmentPython (Join-Path $PSScriptRoot 'verify_environment.py') --quiet --language $Language
    if ($LASTEXITCODE -ne 0) { throw (Text 'Środowisko jest uszkodzone. Zmień nazwę .venv i uruchom ponownie, aby je odtworzyć.' 'The environment is damaged. Rename .venv and restart to prepare it again.') }
    $bootstrapLock.Dispose(); $bootstrapLock = $null
    if ($PrepareOnly -or $CheckOnly) { Write-Host (Text 'Środowisko qNMR Lab jest gotowe.' 'qNMR Lab environment is ready.'); exit 0 }
    & $environmentPython -m qnmr @AppArgs
    if ($LASTEXITCODE -ne 0) { throw (Text "qNMR Lab zakończony kodem $LASTEXITCODE." "qNMR Lab exited with code $LASTEXITCODE.") }
} catch {
    Write-Host ((Text 'BŁĄD: ' 'ERROR: ') + $_.Exception.Message) -ForegroundColor Red
    exit 1
} finally {
    if ($bootstrapLock) { $bootstrapLock.Dispose() }
}

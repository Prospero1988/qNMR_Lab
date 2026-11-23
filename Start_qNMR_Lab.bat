@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\bootstrap.ps1" %*
if errorlevel 1 (
  echo.
  echo Nie mozna uruchomic qNMR Lab. Przeczytaj komunikat powyzej.
  echo qNMR Lab could not start. Please read the error above.
  pause
  exit /b 1
)
endlocal

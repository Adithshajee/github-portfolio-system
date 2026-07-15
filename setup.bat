@echo off
rem ============================================================================
rem GPS Developer Identity Platform Bootstrapping Setup Script (Windows)
rem ============================================================================
setlocal enabledelayedexpansion

echo ============================================================================
echo 🚀 GPS Bootstrapping Setup Workspace Automation
echo ============================================================================

rem 1. Verify Python
echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.10+
    exit /b 1
)
for /f "tokens=2 delims= " %%I in ('python --version') do set pyver=%%I
echo ✓ Python version: !pyver!

rem 2. Verify Git
echo Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git is not installed or not in PATH. Please install Git.
    exit /b 1
)
echo ✓ Git detected.

rem 3. Verify pip
echo Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is not installed. Reinstall Python or enable pip.
    exit /b 1
)
echo ✓ pip detected.

rem 4. Verify Internet
echo Checking internet connection...
ping -n 1 pypi.org >nul 2>&1
if errorlevel 1 (
    echo ❌ Internet connection is offline. Setup requires online packages access.
    exit /b 1
)
echo ✓ Internet connectivity verified.

rem 5. Verify Write Permissions
echo Checking folder write permissions...
echo temp > write_test.tmp
if not exist write_test.tmp (
    echo ❌ Write permissions check failed. Run setup as Administrator or in a writable folder.
    exit /b 1
)
del write_test.tmp
echo ✓ Write permissions verified.

rem 6. Create virtual environment
if not exist .venv (
    echo Creating Python virtual environment ^(.venv^)...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment.
        exit /b 1
      )
)
echo ✓ Virtual environment ready.

rem 7. Activate venv & Install package
echo Activating .venv and installing GPS dependencies...
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,huggingface,kaggle]"
if errorlevel 1 (
    echo ❌ Failed to install GPS packages. Check pip error output.
    exit /b 1
)
echo ✓ Installation completed.

rem 8. Generate configuration gps.yml if missing
if not exist gps.yml (
    echo Generating default gps.yml...
    gps init --non-interactive --force
    if errorlevel 1 (
        echo ❌ Failed to initialize configuration using 'gps init'.
        exit /b 1
    )
) else (
    echo ✓ gps.yml already exists.
)

rem 9. Generate folders and files scaffolding
if not exist profile (
    mkdir profile
)
if not exist profile\README.md (
    echo Creating default profile README.md...
    echo # Developer Profile > profile\README.md
    echo. >> profile\README.md
    echo ^<!-- REPOS_START --^> >> profile\README.md
    echo ^<!-- REPOS_END --^> >> profile\README.md
)
echo ✓ Scaffolding files ready.

rem 10. Run validation pipeline
echo Running system diagnostics checks...
gps doctor
gps verify
if errorlevel 1 (
    echo ⚠️ Health checks failed or reported warnings. Check warnings above.
) else (
    echo ✓ All system checks passed successfully.
)

echo.
echo ============================================================================
echo 🎉 GPS Developer Identity Platform Setup successfully completed!
echo ============================================================================
echo.
echo Next Steps:
echo   1. Activate virtual environment:  .venv\Scripts\activate
echo   2. Run visual dashboard:          gps dashboard
echo   3. Launch preview:                http://localhost:8080
echo.
exit /b 0

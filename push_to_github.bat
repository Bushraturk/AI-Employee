@echo off
echo ============================================================
echo GitHub Push Helper - Silver Tier
echo ============================================================
echo.
echo This script will help you push Silver Tier to GitHub
echo.
echo IMPORTANT: You need a GitHub Personal Access Token
echo.
echo If you don't have one:
echo 1. Go to: https://github.com/settings/tokens/new
echo 2. Create token with 'repo' scope
echo 3. Copy the token
echo.
echo ============================================================
echo.

set /p TOKEN="Enter your GitHub Personal Access Token: "

if "%TOKEN%"=="" (
    echo [ERROR] Token cannot be empty
    pause
    exit /b 1
)

echo.
echo [INFO] Pushing to GitHub...
echo [INFO] Branch: 002-silver-functional
echo [INFO] Repository: https://github.com/Bushraturk/AI-Employee.git
echo.

git push https://%TOKEN%@github.com/Bushraturk/AI-Employee.git 002-silver-functional

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo [SUCCESS] Push completed successfully!
    echo ============================================================
    echo.
    echo Your Silver Tier work is now on GitHub!
    echo.
    echo Next steps:
    echo 1. Go to: https://github.com/Bushraturk/AI-Employee
    echo 2. Create Pull Request from 002-silver-functional to main
    echo 3. Review and merge
    echo.
) else (
    echo.
    echo ============================================================
    echo [ERROR] Push failed!
    echo ============================================================
    echo.
    echo Possible reasons:
    echo 1. Invalid token
    echo 2. Token doesn't have 'repo' scope
    echo 3. Network issue
    echo.
    echo Please check and try again.
    echo.
)

pause

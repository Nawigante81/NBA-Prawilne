@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul 2>&1
echo ================================================
echo NBA Analysis System - Quick Start
echo ================================================
echo.
echo Checking project readiness...
echo.
REM Check if we are in the right directory
if not exist "package.json" (
  echo MISSING
)
echo AFTER

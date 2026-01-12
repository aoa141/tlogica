@echo off
REM Run MSSQL LocalDB Integration Tests for tlogica
REM Requires: SQL Server LocalDB, pyodbc, ODBC Driver 17 or 18

echo ============================================
echo tlogica LocalDB Integration Tests
echo ============================================
echo.

REM Check if pyodbc is installed
python -c "import pyodbc" 2>nul
if errorlevel 1 (
    echo ERROR: pyodbc is not installed.
    echo Please run: pip install pyodbc
    exit /b 1
)

REM Check if pytest is installed
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo ERROR: pytest is not installed.
    echo Please run: pip install pytest
    exit /b 1
)

echo Running tests...
echo.

REM Run the tests with verbose output
python -m pytest "%~dp0integration_tests\mssql_localdb_tests.py" -v %*

echo.
echo ============================================
echo Tests complete
echo ============================================

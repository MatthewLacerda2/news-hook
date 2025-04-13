@echo off
echo Running build and test checks...

echo.
echo Step 1: Checking Python syntax (build check)...
python -m py_compile src/*.py
if %ERRORLEVEL% neq 0 (
    echo Build failed! Python syntax errors found.
    exit /b 1
)

echo.
echo Step 2: Running linting checks...
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
if %ERRORLEVEL% neq 0 (
    echo Linting errors found! Please fix them before proceeding.
    exit /b 1
)
flake8 . --count --max-complexity=10 --max-line-length=127 --statistics
if %ERRORLEVEL% neq 0 (
    echo Linting errors found! Please fix them before proceeding.
    exit /b 1
)

echo.
echo Step 3: Running tests...
pytest
if %ERRORLEVEL% neq 0 (
    echo Tests failed! Please fix them before proceeding.
    exit /b 1
)

echo.
echo All checks passed successfully!
echo You can now mark your PR as ready for review.

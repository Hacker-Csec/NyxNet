@echo off
echo NyxNet Setup Script
echo =================
echo.

echo Step 1: Adding security to chatbox.py...
python chatbox_security.py
if %errorlevel% neq 0 (
    echo Failed to add security to chatbox.py.
    pause
    exit /b 1
)
echo.

echo Step 2: Building executables...
call build_loader.bat
if %errorlevel% neq 0 (
    echo Failed to build executables.
    pause
    exit /b 1
)
echo.

echo Setup completed successfully!
echo.
echo You can find the following files in the 'dist' directory:
echo - NyxNet_Loader.exe
echo - NyxNet.exe
echo.
echo Remember:
echo - Always distribute both files together
echo - Users must launch through NyxNet_Loader.exe
echo - Default password: xyNNet_XOPP^QZKL
echo.

pause 
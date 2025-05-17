@echo off
echo Building NyxNet Secure System...

rem Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo Failed to install PyInstaller. Please install it manually.
        pause
        exit /b 1
    )
)

rem Make sure we have the required packages
echo Installing requirements...
pip install requests customtkinter
if %errorlevel% neq 0 (
    echo Failed to install required packages.
    pause
    exit /b 1
)

rem Create output directory
if not exist "dist" mkdir dist

rem Build the loader executable
echo Building NyxNet Loader...
pyinstaller --noconfirm --onefile --windowed --icon=logo.png --name="NyxNet_Loader" --add-data="logo.png;." nyx_updater.py
if %errorlevel% neq 0 (
    echo Failed to build loader executable.
    pause
    exit /b 1
)

rem Build the main application executable
echo Building NyxNet main application...
pyinstaller --noconfirm --onefile --windowed --icon=logo.png --name="NyxNet" --add-data="logo.png;." NyxNet_main.py
if %errorlevel% neq 0 (
    echo Failed to build main application executable.
    pause
    exit /b 1
)

rem Rename the executables for clarity
move /y "dist\NyxNet_Loader.exe" "dist\NyxNet_Loader.exe" >nul 2>&1
move /y "dist\NyxNet.exe" "dist\NyxNet.exe" >nul 2>&1

echo.
echo Build completed successfully!
echo.
echo The loader and main application are located in the 'dist' folder:
echo - NyxNet_Loader.exe: The secure loader application
echo - NyxNet.exe: The main application (only launches through loader)
echo.
echo INSTRUCTIONS:
echo 1. Distribute both files together
echo 2. Users should ONLY run NyxNet_Loader.exe
echo 3. The authentication password is: xyNNet_XOPP^QZKL
echo.

pause 
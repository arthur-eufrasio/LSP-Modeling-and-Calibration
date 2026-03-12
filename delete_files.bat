@echo off
REM Script to clear specific directories while keeping .gitkeep files

set "BASE_DIR=backend\"

REM Clean cae directory
echo Cleaning %BASE_DIR%\files\cae...
for %%i in ("%BASE_DIR%\files\cae\*") do (
    if /I not "%%~nxi"==".gitkeep" del /q "%%i"
)

REM Clean inp directory
echo Cleaning %BASE_DIR%\files\inp...
for %%i in ("%BASE_DIR%\files\inp\*") do (
    if /I not "%%~nxi"==".gitkeep" del /q "%%i"
)

REM Clean job directory
echo Cleaning %BASE_DIR%\files\job...
for %%i in ("%BASE_DIR%\files\job\*") do (
    if /I not "%%~nxi"==".gitkeep" del /q "%%i"
)

REM Clean data directory
echo Cleaning %BASE_DIR%\data...
for %%i in ("%BASE_DIR%\data\*") do (
    if /I not "%%~nxi"==".gitkeep" del /q "%%i"
)

REM Clean log directory
echo Cleaning %BASE_DIR%\log...
for %%i in ("%BASE_DIR%\log\*") do (
    if /I not "%%~nxi"==".gitkeep" del /q "%%i"
)

echo.
echo Cleanup process finished successfully!

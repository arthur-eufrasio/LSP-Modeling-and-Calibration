@echo off
REM Script to clear all files from specific directories

set "BASE_DIR=backend\"

REM Clean cae directory
echo Cleaning %BASE_DIR%\files\cae...
del /q /f "%BASE_DIR%\files\cae\*"

REM Clean inp directory
echo Cleaning %BASE_DIR%\files\inp...
del /q /f "%BASE_DIR%\files\inp\*"

REM Clean job directory
echo Cleaning %BASE_DIR%\files\job...
del /q /f "%BASE_DIR%\files\job\*"

REM Clean data directory
echo Cleaning %BASE_DIR%\data...
del /q /f "%BASE_DIR%\data\*"

REM Clean log directory
echo Cleaning %BASE_DIR%\log...
del /q /f "%BASE_DIR%\log\*"

echo.
echo Cleanup process finished successfully!
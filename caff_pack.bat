@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~1"
if "%ROOT_DIR%"=="" set "ROOT_DIR=."
set "TOOL_PATH=caff_tool.py"

echo Recursively packing 'default.toml' -^> 'default.bin' in "%ROOT_DIR%"...
for /R "%ROOT_DIR%" %%F in (default.toml) do (
    if exist "%%F" (
        set "TOML_PATH=%%F"
        set "DIR_PATH=%%~dpF"
        set "BIN_PATH=!DIR_PATH!default.bin"
        echo Packing: "!TOML_PATH!" -^> "!BIN_PATH!"
        python "%TOOL_PATH%" pack "!TOML_PATH!" "!BIN_PATH!"
    )
)
endlocal

pause
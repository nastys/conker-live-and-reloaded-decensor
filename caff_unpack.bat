@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~1"
if "%ROOT_DIR%"=="" set "ROOT_DIR=."
set "TOOL_PATH=caff_tool.py"

echo Recursively unpacking 'default.bin' -^> 'default.toml' in "%ROOT_DIR%"...
for /R "%ROOT_DIR%" %%F in (default.bin) do (
    if exist "%%F" (
        set "BIN_PATH=%%F"
        set "DIR_PATH=%%~dpF"
        set "TOML_PATH=!DIR_PATH!default.toml"
        echo Unpacking: "!BIN_PATH!" -^> "!TOML_PATH!"
        python "%TOOL_PATH%" unpack "!BIN_PATH!" "!TOML_PATH!"
    )
)
endlocal

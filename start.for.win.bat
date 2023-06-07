@echo off

set ENVPATH=%~dp0/env

if not exist "%ENVPATH%" (
    call python -m venv env
)

call "%ENVPATH%\Scripts\activate.bat"
call python -m pip install --upgrade pip
call pip install -r requirements.txt
call python app.py

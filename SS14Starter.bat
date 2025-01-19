@echo off

cd %~dp0

call %~dp0\.venv\Scripts\Activate.bat

python ss14Starter.py %1 %2 %3 %4

deactivate

pause
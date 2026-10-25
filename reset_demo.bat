@echo off
cd /d "%~dp0"
echo Yeh demo ka saara data (ledger, reviews, evidence clips) delete kar dega.
choice /M "You are sure that you have to delete this"
if errorlevel 2 exit /b

del /q ledger.jsonl 2>nul
del /q reviews.jsonl 2>nul
del /q evidence\*.mp4 2>nul
echo Done. you can start your new demo.
pause
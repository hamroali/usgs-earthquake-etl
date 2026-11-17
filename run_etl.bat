@echo off
REM Task Scheduler shu faylni har kuni ishga tushiradi
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
"C:\Users\hp\AppData\Local\Programs\Python\Python314\python.exe" main.py >> logs\scheduler.log 2>&1

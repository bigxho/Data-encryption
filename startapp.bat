@echo off
rem @start cmd
@cls
@cd /D %~dp0
@ping -n 2 127.0.0.1 >null
@cls
rem @start "C:\Program Files\Mozilla Firefox\firefox.exe" http://127.0.0.1:8000/
@call .\penv\Scripts\activate
rem
@echo Starting webapp Djanngo5
@ping -n 3 127.0.0.1 >null
python manage.py runserver | @start "C:\Program Files\Mozilla Firefox\firefox.exe" http://127.0.0.1:8000/
rem
rem @start "C:\Program Files\Mozilla Firefox\firefox.exe" http://127.0.0.1:8000/

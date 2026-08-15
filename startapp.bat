@echo off
rem @start cmd
@cls
@cd /D %~dp0
@ping -n 2 127.0.0.1 >null
@cls
rem
@call .\penv\Scripts\activate
rem
@echo Starting webapp Djanngo5
@ping -n 3 127.0.0.1 >null
python manage.py runserver | @start "%programfiles%\Mozilla Firefox\firefox.exe" http://127.0.0.1:8000/
rem
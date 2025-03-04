@echo off
call venv\Scripts\activate.bat
uvicorn src.main:app --reload --port 8000

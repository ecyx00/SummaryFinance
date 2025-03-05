@echo off
call venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
python -m uvicorn src.app:app --reload --port 8000

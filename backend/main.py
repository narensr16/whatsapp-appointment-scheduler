"""
Entrypoint wrapper for running the backend directly with `python main.py`
as specified in the challenge instructions.
"""
import sys
import os
import uvicorn

# Ensure the backend directory is in the import path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.main import app
from app.config import settings

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

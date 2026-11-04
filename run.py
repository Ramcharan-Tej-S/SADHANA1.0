# run.py — ExamFlow AI launcher
"""Start the ExamFlow AI server: `python run.py` then open http://127.0.0.1:8000"""
import os
import sys
import webbrowser

import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HOST = os.environ.get("EXAMFLOW_HOST", "127.0.0.1")
PORT = int(os.environ.get("EXAMFLOW_PORT", "8000"))

if __name__ == "__main__":
    url = f"http://{HOST}:{PORT}"
    print("=" * 60)
    print("  EXAMFLOW AI  --  INSERT COIN")
    print(f"  {url}")
    print("=" * 60)
    if os.environ.get("EXAMFLOW_OPEN", "1") == "1":
        webbrowser.open(url)
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False)

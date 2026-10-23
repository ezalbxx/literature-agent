"""
AI科学文献研究智能体 - 一键启动脚本
同时启动 FastAPI 后端 (端口 8000) 和 Streamlit 前端 (端口 8501)
"""

import subprocess
import sys
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))


def check_health(url: str, retries: int = 30, interval: float = 1.0) -> bool:
    """轮询健康检查"""
    for i in range(retries):
        try:
            resp = urllib.request.urlopen(url, timeout=2)
            return resp.status == 200
        except Exception:
            pass
        time.sleep(interval)
    return False


def main():
    print("=" * 60)
    print("AI Scientific Literature Research Agent - Starting...")
    print("=" * 60)

    # 启动后端
    print("\n[1/2] Starting FastAPI backend (port 8000)...")
    backend_proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "backend.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--log-level", "warning",
        ],
        cwd=ROOT,
    )

    # 等待并验证后端启动
    print("  Waiting for backend...", end="", flush=True)
    if not check_health("http://localhost:8000/api/health"):
        print("\n  ERROR: Backend failed to start!")
        backend_proc.terminate()
        sys.exit(1)
    print(" OK")
    print("  Backend:  http://localhost:8000")
    print("  API docs: http://localhost:8000/docs")

    # 启动前端
    print("\n[2/2] Starting Streamlit frontend (port 8501)...")
    frontend_proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "frontend/app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
        ],
        cwd=ROOT,
    )

    # 等待前端启动
    print("  Waiting for frontend...", end="", flush=True)
    if not check_health("http://localhost:8501/_stcore/health", retries=15, interval=1.0):
        print("\n  WARNING: Frontend may not have started. Check the output above for errors.")
    else:
        print(" OK")

    print("\n" + "=" * 60)
    print("All services started!")
    print("  Frontend: http://localhost:8501")
    print("  Backend:  http://localhost:8000/docs")
    print("  Press Ctrl+C to stop all services")
    print("=" * 60)

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("All services stopped.")


if __name__ == "__main__":
    main()

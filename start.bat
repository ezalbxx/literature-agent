@echo off
chcp 65001 >nul
echo ============================================
echo AI科学文献研究智能体 - 安装与启动
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] 安装根目录依赖...
python -m pip install -r requirements.txt
echo.

echo [2/4] 安装后端依赖...
rem Backend requirements are included in root requirements.txt.
echo.

echo [3/4] 安装前端依赖...
rem Frontend requirements are included in root requirements.txt.
echo.

echo [4/4] 启动服务...
echo.
echo ============================================
echo 后端 API:  http://localhost:8000/docs
echo 前端应用:  http://localhost:8501
echo ============================================
echo.

python run.py
pause

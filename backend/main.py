"""
FastAPI 后端入口
AI科学文献研究智能体 - REST API Server
"""

import sys
import os

# Windows GBK 编码兼容 - 强制 UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 确保项目根目录在 Python 路径中，以便导入 agents/tools/utils/config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_NAME, APP_VERSION, APP_DESCRIPTION
from backend.routers import health, literature, gap, experiment, paper, history, library, workspaces

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION + " - REST API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置 - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(health.router)
app.include_router(literature.router)
app.include_router(gap.router)
app.include_router(experiment.router)
app.include_router(paper.router)
app.include_router(history.router)
app.include_router(library.router)
app.include_router(workspaces.router)


@app.on_event("startup")
def startup_event():
    """后端启动事件"""
    print(f"🔬 {APP_NAME} v{APP_VERSION}")
    print(f"📡 API 文档: http://localhost:8000/docs")
    print(f"🤖 LLM Provider: DeepSeek-Chat")
    print(f"📚 数据源: PubMed + arXiv")

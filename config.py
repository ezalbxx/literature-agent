"""
AI科学文献研究智能体 - 配置文件
Configuration for AI Scientific Literature Research Agent
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# LLM Configuration (支持多种LLM后端)
# ============================================================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")  # "deepseek" | "anthropic" | "openai"

# DeepSeek Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

# Anthropic (Claude) Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ============================================================
# PubMed Configuration
# ============================================================
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL", "researcher@example.com")
PUBMED_API_KEY = os.getenv("PUBMED_API_KEY", "")  # Optional, increases rate limit
PUBMED_MAX_RESULTS = int(os.getenv("PUBMED_MAX_RESULTS", "50"))

# ============================================================
# arXiv Configuration
# ============================================================
ARXIV_MAX_RESULTS = int(os.getenv("ARXIV_MAX_RESULTS", "30"))

# ============================================================
# Application Configuration
# ============================================================
APP_NAME = "AI科学文献研究智能体"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "跨库文献检索 | 研究空白探测 | 实验方案设计 | 论文写作辅助"

# Data Storage
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Search History File
SEARCH_HISTORY_FILE = os.path.join(DATA_DIR, "search_history.json")

# Default Language
DEFAULT_LANGUAGE = "zh"  # "zh" | "en"

# Supported Journal Styles
JOURNAL_STYLES = [
    "Nature",
    "Science",
    "Cell",
    "PNAS",
    "IEEE",
    "ACM",
    "Elsevier",
    "Springer",
    "PLOS ONE",
    "通用学术规范 (General Academic)",
]

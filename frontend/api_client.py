"""
前端 API 客户端
封装所有对后端 REST API 的 HTTP 调用
"""

import requests
import os
from typing import Dict, List, Any, Optional

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8000').rstrip('/')
TIMEOUT = 300  # LLM 调用可能较慢，设置较长超时


class APIError(Exception):
    """API 调用错误"""
    pass


class APIClient:
    """后端 API HTTP 客户端"""

    # ============================================================
    # 内部工具方法
    # ============================================================

    @staticmethod
    def _post(endpoint: str, payload: dict) -> dict:
        """内部方法：POST 请求"""
        try:
            resp = requests.post(
                f"{BACKEND_URL}{endpoint}",
                json=payload,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise APIError("无法连接到后端服务。请确保后端已启动 (python backend/main.py)。")
        except requests.exceptions.Timeout:
            raise APIError("请求超时。LLM 生成可能需要较长时间，请稍后重试。")
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = str(e)
            raise APIError(f"API 错误 [{e.response.status_code}]: {detail}")
        except Exception as e:
            raise APIError(f"请求失败: {str(e)}")

    @staticmethod
    def _get(endpoint: str) -> dict:
        """内部方法：GET 请求"""
        try:
            resp = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise APIError("无法连接到后端服务。请确保后端已启动。")
        except Exception as e:
            raise APIError(f"请求失败: {str(e)}")

    # ============================================================
    # 健康检查
    # ============================================================

    @staticmethod
    def health() -> dict:
        """健康检查"""
        return APIClient._get("/api/health")

    # ============================================================
    # 文献检索
    # ============================================================

    @staticmethod
    def literature_search(query: str, pubmed_max: int = 30, arxiv_max: int = 20) -> dict:
        """跨库检索文献（仅检索）"""
        return APIClient._post("/api/literature/search", {
            "query": query,
            "pubmed_max": pubmed_max,
            "arxiv_max": arxiv_max,
        })

    @staticmethod
    def literature_search_and_review(query: str, pubmed_max: int = 30, arxiv_max: int = 20) -> dict:
        """一站式：检索 + 综述 + 摘要"""
        return APIClient._post("/api/literature/search-and-review", {
            "query": query,
            "pubmed_max": pubmed_max,
            "arxiv_max": arxiv_max,
        })

    @staticmethod
    def literature_export_bibtex(articles: List[Dict[str, Any]]) -> dict:
        """导出 BibTeX"""
        return APIClient._post("/api/literature/export-bibtex", {
            "articles": articles,
        })

    # ============================================================
    # 研究空白分析
    # ============================================================

    @staticmethod
    def gap_analyze(topic: str, deep_search: bool = True) -> dict:
        """完整分析：热点 + 趋势 + 空白"""
        return APIClient._post("/api/gap/analyze", {
            "topic": topic,
            "deep_search": deep_search,
        })

    @staticmethod
    def gap_hotspots(topic: str) -> dict:
        """仅热点分析"""
        return APIClient._post("/api/gap/hotspots", {"topic": topic})

    @staticmethod
    def gap_detect(topic: str) -> dict:
        """仅空白探测"""
        return APIClient._post("/api/gap/detect-gaps", {"topic": topic})

    # ============================================================
    # 实验方案设计
    # ============================================================

    @staticmethod
    def experiment_design(research_question: str, search_methods: bool = True) -> dict:
        """生成实验设计方案"""
        return APIClient._post("/api/experiment/design", {
            "research_question": research_question,
            "search_methods": search_methods,
        })

    @staticmethod
    def experiment_recommend_methods(research_question: str) -> dict:
        """推荐实验方法"""
        return APIClient._post("/api/experiment/recommend-methods", {
            "research_question": research_question,
        })

    @staticmethod
    def experiment_design_with_recommendations(research_question: str) -> dict:
        """一站式：方法推荐 + 完整设计"""
        return APIClient._post("/api/experiment/design-with-recommendations", {
            "research_question": research_question,
        })

    @staticmethod
    def experiment_validate(design_text: str) -> dict:
        """验证设计完整性"""
        return APIClient._post("/api/experiment/validate", {
            "design_text": design_text,
        })

    # ============================================================
    # 论文写作辅助
    # ============================================================

    @staticmethod
    def paper_generate_section(section: str, context: Dict[str, Any], style: str = "通用学术规范") -> dict:
        """生成单个章节"""
        return APIClient._post("/api/paper/generate-section", {
            "section": section,
            "context": context,
            "style": style,
        })

    @staticmethod
    def paper_generate_full(context: Dict[str, Any], style: str = "通用学术规范") -> dict:
        """生成完整论文"""
        return APIClient._post("/api/paper/generate-full", {
            "context": context,
            "style": style,
        })

    @staticmethod
    def paper_writing_tips(section: str, style: str = "通用学术规范") -> dict:
        """获取写作提示"""
        return APIClient._post("/api/paper/writing-tips", {
            "section": section,
            "style": style,
        })

    @staticmethod
    def paper_format_check(text: str, style: str = "通用学术规范") -> dict:
        """检查格式"""
        return APIClient._post("/api/paper/format-check", {
            "text": text,
            "style": style,
        })

    # ============================================================
    # 历史记录管理
    # ============================================================

    @staticmethod
    def history_save(module: str, title: str, query: str, data: Dict[str, Any]) -> dict:
        """保存查询结果"""
        return APIClient._post("/api/history/save", {
            "module": module,
            "title": title,
            "query": query,
            "data": data,
        })

    @staticmethod
    def history_list(module: str = None) -> dict:
        """列出已保存结果"""
        params = ""
        if module:
            params = f"?module={module}"
        return APIClient._get(f"/api/history/list{params}")

    @staticmethod
    def history_get(item_id: str) -> dict:
        """获取保存记录详情"""
        return APIClient._get(f"/api/history/get/{item_id}")

    @staticmethod
    def history_delete(item_id: str) -> dict:
        """删除保存记录"""
        try:
            resp = requests.delete(
                f"{BACKEND_URL}/api/history/delete/{item_id}",
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise APIError(f"删除失败: {str(e)}")

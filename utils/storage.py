"""
本地存储管理 - 保存和读取所有查询结果
使用 JSON 文件存储在 data/saved/ 目录下
"""

import json
import os
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from config import DATA_DIR

SAVED_DIR = os.path.join(DATA_DIR, "saved")
os.makedirs(SAVED_DIR, exist_ok=True)


def _generate_id() -> str:
    """生成唯一 ID"""
    return uuid.uuid4().hex[:12]


def save_result(
    module: str,
    title: str,
    query: str,
    data: Dict[str, Any],
) -> str:
    """
    保存查询结果

    Args:
        module: 模块类型 (literature/gap/experiment/paper)
        title: 保存标题
        query: 原始查询
        data: 完整结果数据

    Returns:
        保存项 ID
    """
    item_id = _generate_id()
    timestamp = datetime.now().isoformat()

    record = {
        "id": item_id,
        "module": module,
        "title": title,
        "query": query,
        "timestamp": timestamp,
        "data": data,
    }

    filepath = os.path.join(SAVED_DIR, f"{item_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return item_id


def list_saved(module: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    列出已保存的结果

    Args:
        module: 可选，按模块筛选
        limit: 最大返回数

    Returns:
        保存项列表（不含完整data，仅含摘要信息）
    """
    items = []
    for filename in os.listdir(SAVED_DIR):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(SAVED_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                record = json.load(f)
        except Exception:
            continue

        if module and record.get("module") != module:
            continue

        # 返回摘要（不含完整data，减少传输）
        items.append({
            "id": record["id"],
            "module": record["module"],
            "title": record["title"],
            "query": record["query"],
            "timestamp": record["timestamp"],
            "preview": _get_preview(record),
        })

    items.sort(key=lambda x: x["timestamp"], reverse=True)
    return items[:limit]


def get_saved(item_id: str) -> Optional[Dict[str, Any]]:
    """获取完整的保存记录"""
    if not re.fullmatch(r'[0-9a-f]{12}', item_id):
        return None
    filepath = os.path.join(SAVED_DIR, f"{item_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_saved(item_id: str) -> bool:
    """删除保存记录"""
    if not re.fullmatch(r'[0-9a-f]{12}', item_id):
        return False
    filepath = os.path.join(SAVED_DIR, f"{item_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


def _get_preview(record: Dict) -> str:
    """生成预览摘要"""
    module = record.get("module", "")
    data = record.get("data", {})

    if module == "literature":
        n = len(data.get("articles", []))
        return f"检索到 {n} 篇文献 (PubMed: {data.get('total_pubmed', 0)}, arXiv: {data.get('total_arxiv', 0)})"
    elif module == "gap":
        return f"热点关键词: {', '.join(data.get('hot_keywords', [])[:5]) or '无'}"
    elif module == "experiment":
        text = data.get("full_design", "")[:100]
        return text + "..." if len(text) >= 100 else text
    elif module == "paper":
        sections = [k for k in ["abstract", "introduction", "methods", "results", "discussion"]
                    if data.get(k)]
        return f"已生成: {', '.join(sections)}" if sections else "无内容"
    return ""

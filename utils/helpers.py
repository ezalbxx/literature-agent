"""
工具函数模块 - Helper utility functions
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional


def sanitize_filename(name: str) -> str:
    """清理文件名，移除非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def save_json(data: Any, filepath: str) -> None:
    """保存数据为JSON文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> Optional[Any]:
    """从JSON文件加载数据"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_date(date_str: str) -> str:
    """格式化日期字符串"""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return date_str


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """简单的关键词提取（基于词频）"""
    # 移除标点符号
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()

    # 停用词
    stopwords = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'shall', 'to', 'of', 'in', 'for',
        'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'and', 'but', 'or',
        'nor', 'not', 'so', 'yet', 'both', 'either', 'neither', 'each', 'every',
        'all', 'any', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
        'only', 'own', 'same', 'than', 'too', 'very', 'just', 'because',
        'about', 'also', 'this', 'that', 'these', 'those', 'it', 'its',
        'we', 'they', 'them', 'their', 'he', 'she', 'his', 'her', 'which',
        'who', 'whom', 'what', 'when', 'where', 'how', 'if', 'then', 'else',
        'et', 'al', 'using', 'based', 'study', 'research', 'results', 'show',
        'found', 'used', 'method', 'data', 'analysis', 'significant',
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
        '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
        '没有', '看', '好', '自己', '这',
    }

    # 词频统计
    word_freq = {}
    for word in words:
        if len(word) > 2 and word not in stopwords:
            word_freq[word] = word_freq.get(word, 0) + 1

    # 按频率排序
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]


def truncate_text(text: str, max_length: int = 500) -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'


def build_citation(metadata: Dict[str, Any], style: str = "APA") -> str:
    """根据元数据生成引文"""
    authors = metadata.get('authors', ['Unknown'])
    title = metadata.get('title', 'Untitled')
    year = metadata.get('year', 'n.d.')
    journal = metadata.get('journal', '')
    doi = metadata.get('doi', '')

    if style == "APA":
        first_author = authors[0].split()[-1] if authors else 'Unknown'
        if len(authors) > 1:
            first_author += ' et al.'
        citation = f"{first_author} ({year}). {title}."
        if journal:
            citation += f" *{journal}*."
        if doi:
            citation += f" https://doi.org/{doi}"
        return citation

    elif style == "Vancouver":
        citation = ", ".join(authors[:3])
        if len(authors) > 3:
            citation += " et al."
        citation += f". {title}."
        if journal:
            citation += f" {journal}."
        citation += f" {year}."
        if doi:
            citation += f" doi:{doi}"
        return citation

    else:
        return f"{', '.join(authors)} ({year}). {title}. {journal}."


def parse_pubmed_date(pubmed_date_str: str) -> str:
    """解析PubMed日期格式"""
    # PubMed日期格式多样: YYYY, YYYY Mon, YYYY Mon DD, etc.
    pubmed_date_str = pubmed_date_str.strip()
    try:
        dt = datetime.strptime(pubmed_date_str, '%Y %b %d')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        try:
            dt = datetime.strptime(pubmed_date_str, '%Y %b')
            return dt.strftime('%Y-%m')
        except ValueError:
            try:
                dt = datetime.strptime(pubmed_date_str, '%Y')
                return pubmed_date_str
            except ValueError:
                return pubmed_date_str


class SearchHistory:
    """搜索历史管理器"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.history = self._load()

    def _load(self) -> List[Dict]:
        return load_json(self.filepath) or []

    def add(self, query: str, source: str, results_count: int) -> None:
        self.history.append({
            'query': query,
            'source': source,
            'results_count': results_count,
            'timestamp': datetime.now().isoformat(),
        })
        self._save()

    def _save(self) -> None:
        save_json(self.history, self.filepath)

    def get_recent(self, limit: int = 20) -> List[Dict]:
        return self.history[-limit:]

    def clear(self) -> None:
        self.history = []
        self._save()

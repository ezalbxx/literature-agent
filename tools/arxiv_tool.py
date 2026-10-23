"""
arXiv API 集成工具
提供arXiv文献检索、摘要获取等功能
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET

import requests
import arxiv

from config import ARXIV_MAX_RESULTS


class ArxivTool:
    """arXiv API 封装"""

    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self):
        self.max_results = ARXIV_MAX_RESULTS

    def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        搜索arXiv并返回文献信息

        Args:
            query: 搜索查询字符串
            max_results: 最大结果数

        Returns:
            文献信息列表
        """
        if max_results is None:
            max_results = self.max_results

        try:
            # 使用arxiv官方库
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )

            results = []
            for result in client.results(search):
                info = self._parse_result(result)
                results.append(info)

            return results

        except Exception as e:
            # 回退到直接API调用
            return self._fallback_search(query, max_results)

    def _parse_result(self, result) -> Dict[str, Any]:
        """解析arxiv.Result对象"""
        # 提取arxiv ID
        arxiv_id = result.entry_id.split('/')[-1]
        # 移除版本号
        if 'v' in arxiv_id:
            arxiv_id = arxiv_id[:arxiv_id.rindex('v')]

        # 日期
        published = result.published
        year = str(published.year) if published else ''

        # 分类
        categories = [c for c in result.categories] if result.categories else []

        # 摘要
        abstract = result.summary.replace('\n', ' ').strip() if result.summary else ''

        # 作者
        authors = [a.name for a in result.authors] if result.authors else []

        # PDF链接
        pdf_url = result.pdf_url if result.pdf_url else ''

        return {
            'source': 'arXiv',
            'arxiv_id': arxiv_id,
            'title': result.title or 'No Title Available',
            'abstract': abstract,
            'authors': authors,
            'date': published.strftime('%Y-%m-%d') if published else '',
            'year': year,
            'journal': 'arXiv preprint',
            'doi': result.doi or '',
            'keywords': categories,
            'url': result.entry_id or f"https://arxiv.org/abs/{arxiv_id}",
            'pdf_url': pdf_url,
        }

    def _fallback_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """备用搜索方法：直接使用arXiv API"""
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending',
        }

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            resp.raise_for_status()

            root = ET.fromstring(resp.text)
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom',
            }

            results = []
            for entry in root.findall('atom:entry', ns):
                arxiv_id = entry.find('atom:id', ns).text.split('/')[-1]
                if 'v' in arxiv_id:
                    arxiv_id = arxiv_id[:arxiv_id.rindex('v')]

                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                abstract = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')

                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns).text
                    authors.append(name)

                published = entry.find('atom:published', ns).text
                published_date = published[:10] if published else ''

                categories = []
                for cat in entry.findall('arxiv:primary_category', ns):
                    categories.append(cat.get('term', ''))

                link = entry.find('atom:link[@title="pdf"]', ns)
                pdf_url = link.get('href', '') if link is not None else ''

                results.append({
                    'source': 'arXiv',
                    'arxiv_id': arxiv_id,
                    'title': title,
                    'abstract': abstract,
                    'authors': authors,
                    'date': published_date,
                    'year': published_date[:4] if published_date else '',
                    'journal': 'arXiv preprint',
                    'doi': '',
                    'keywords': categories,
                    'url': f"https://arxiv.org/abs/{arxiv_id}",
                    'pdf_url': pdf_url,
                })

            return results

        except Exception as e:
            raise RuntimeError('arXiv search unavailable') from None

    def search_by_category(self, category: str, max_results: int = None) -> List[Dict[str, Any]]:
        """按学科分类搜索最新论文"""
        query = f"cat:{category}"
        return self.search(query, max_results)

    def get_recent(self, topic: str, days: int = 30, max_results: int = None) -> List[Dict[str, Any]]:
        """获取最近N天的相关论文"""
        if max_results is None:
            max_results = self.max_results

        query = f"all:{topic}"
        return self.search(query, max_results)

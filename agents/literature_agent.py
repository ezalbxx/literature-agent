"""
文献检索与摘要智能体
Literature Search & Summarization Agent

功能：
1. 跨库检索：PubMed + arXiv
2. 结构化文献综述生成
3. 简明摘要生成
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import re
import unicodedata

from tools.pubmed_tool import PubMedTool
from tools.arxiv_tool import ArxivTool
from tools.llm_tool import LLMTool


@dataclass
class SearchResult:
    """检索结果数据结构"""
    query: str
    total_pubmed: int
    total_arxiv: int
    articles: List[Dict[str, Any]]
    structured_review: str = ""
    abstract_summary: str = ""
    source_status: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


class LiteratureAgent:
    """
    跨库文献智能检索与摘要智能体

    支持:
    - PubMed 和 arXiv 双库检索
    - 结构化的文献综述生成
    - 简明研究摘要生成
    """

    def __init__(self, pubmed=None, arxiv=None, llm=None):
        self.pubmed = pubmed if pubmed is not None else PubMedTool()
        self.arxiv = arxiv if arxiv is not None else ArxivTool()
        self._llm = llm
        self.source_status = {}
        self.warnings = []

    @property
    def llm(self):
        # Retrieval and BibTeX export work without model credentials.
        if self._llm is None:
            self._llm = LLMTool()
        return self._llm

    def cross_search(self, query: str,
                     pubmed_max: int = 30,
                     arxiv_max: int = 20) -> List[Dict[str, Any]]:
        """
        跨库检索文献

        Args:
            query: 搜索查询
            pubmed_max: PubMed最大结果数
            arxiv_max: arXiv最大结果数

        Returns:
            合并去重后的文献列表
        """
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ValueError('query must contain 1–2000 characters')
        for value, limit in [(pubmed_max, 100), (arxiv_max, 50)]:
            if type(value) is not int or not 0 <= value <= limit:
                raise ValueError('Invalid source result limit')
        self.source_status, self.warnings = {}, []
        all_articles = []
        calls = [('PubMed', self.pubmed.search_and_fetch, pubmed_max),
                 ('arXiv', self.arxiv.search, arxiv_max)]
        with ThreadPoolExecutor(max_workers=2) as executor:
            pending = [(name, executor.submit(fn, query.strip(), limit))
                       for name, fn, limit in calls if limit]
            for name, _, limit in calls:
                if not limit:
                    self.source_status[name] = {'status': 'skipped', 'count': 0}
            for name, future in pending:
                try:
                    records = [a for a in future.result()
                               if isinstance(a, dict) and str(a.get('title', '')).strip()]
                    all_articles.extend(records)
                    self.source_status[name] = {'status': 'ok', 'count': len(records)}
                except Exception:
                    self.source_status[name] = {'status': 'failed', 'count': 0}
                    self.warnings.append(f'{name} 检索失败；可用结果可能不完整。')
        def year(a):
            match = re.search(r'\d{4}', str(a.get('year', '')))
            return int(match.group()) if match else 0
        all_articles.sort(key=year, reverse=True)
        seen_dois, seen_titles, unique = set(), set(), []
        for article in all_articles:
            title = ''.join(c for c in unicodedata.normalize('NFKC', article['title']).casefold()
                            if c.isalnum())
            doi = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '',
                         str(article.get('doi', '')).strip().casefold())
            duplicate = (doi and doi in seen_dois) or (title and title in seen_titles)
            if doi:
                seen_dois.add(doi)
            if title:
                seen_titles.add(title)
            if not duplicate:
                unique.append(article)
        return unique

    def search_and_review(self, query: str,
                          pubmed_max: int = 30,
                          arxiv_max: int = 20) -> SearchResult:
        """
        一站式：检索 + 生成综述 + 生成摘要

        Args:
            query: 搜索查询
            pubmed_max: PubMed最大结果数
            arxiv_max: arXiv最大结果数

        Returns:
            SearchResult对象，包含所有结果
        """
        # Step 1: 检索
        articles = self.cross_search(query, pubmed_max, arxiv_max)

        if not articles:
            return SearchResult(
                query=query,
                total_pubmed=0,
                total_arxiv=0,
                articles=[],
                structured_review="检索服务异常，请重试。" if self.warnings else "未检索到相关文献。请尝试调整搜索关键词。",
                abstract_summary="",
                source_status=self.source_status,
                warnings=self.warnings,
            )

        pubmed_count = sum(1 for a in articles if a.get('source') == 'PubMed')
        arxiv_count = sum(1 for a in articles if a.get('source') == 'arXiv')

        # Step 2: 生成结构化综述
        structured_review = self.llm.generate_structured_review(query, articles)

        # Step 3: 生成简明摘要
        abstract_summary = self.llm.generate_abstract_summary(query, articles)

        return SearchResult(
            query=query,
            total_pubmed=pubmed_count,
            total_arxiv=arxiv_count,
            articles=articles,
            structured_review=structured_review,
            abstract_summary=abstract_summary,
            source_status=self.source_status,
            warnings=self.warnings,
        )

    def get_article_detail(self, article_index: int,
                           articles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        获取单篇文献的详细信息

        Args:
            article_index: 文献在列表中的索引
            articles: 文献列表

        Returns:
            文献详情
        """
        if 0 <= article_index < len(articles):
            return articles[article_index]
        return None

    def export_bibtex(self, articles: List[Dict[str, Any]]) -> str:
        """
        导出BibTeX格式的参考文献

        Args:
            articles: 文献列表

        Returns:
            BibTeX格式文本
        """
        bib_entries = []
        for i, article in enumerate(articles):
            authors = article.get('authors', ['Unknown'])
            first_author = authors[0].split()[-1] if authors else 'Unknown'
            year = article.get('year', '0000')
            title = article.get('title', 'Untitled')
            source = article.get('source', '')
            journal = article.get('journal', '')
            doi = article.get('doi', '')
            url = article.get('url', '')

            # 构建BibTeX key
            cite_key = f"ref{i+1}"

            def escape(value):
                return str(value).replace('\\', r'\textbackslash{}').replace('{', r'\{').replace('}', r'\}').replace('\n', ' ')

            entry = f"@article{{{cite_key},\n"
            entry += f"  title = {{{escape(title)}}},\n"
            entry += f"  author = {{{' and '.join(escape(a) for a in authors)}}},\n"
            entry += f"  year = {{{escape(year)}}},\n"
            if journal:
                entry += f"  journal = {{{escape(journal)}}},\n"
            if doi:
                entry += f"  doi = {{{escape(doi)}}},\n"
            if url:
                entry += f"  url = {{{escape(url)}}},\n"
            entry += "}\n"
            bib_entries.append(entry)

        return '\n'.join(bib_entries)

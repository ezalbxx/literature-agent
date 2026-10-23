"""
PubMed API 集成工具
提供PubMed文献检索、摘要获取等功能
"""

import time
from typing import List, Dict, Any, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from config import PUBMED_EMAIL, PUBMED_API_KEY, PUBMED_MAX_RESULTS
from utils.helpers import parse_pubmed_date


class PubMedTool:
    """PubMed / NCBI Entrez API 封装"""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self):
        self.email = PUBMED_EMAIL
        self.api_key = PUBMED_API_KEY
        self.max_results = PUBMED_MAX_RESULTS

    def _build_params(self, extra: Dict = None) -> Dict:
        """构建API请求参数"""
        params = {
            'email': self.email,
            'tool': 'AI-Scientific-Literature-Agent',
        }
        if self.api_key:
            params['api_key'] = self.api_key
        if extra:
            params.update(extra)
        return params

    def search(self, query: str, max_results: int = None) -> List[str]:
        """
        搜索PubMed并返回匹配的PubMed ID列表

        Args:
            query: 搜索查询字符串
            max_results: 最大结果数

        Returns:
            PubMed ID列表 (PMIDs)
        """
        if max_results is None:
            max_results = self.max_results

        # E-search
        params = self._build_params({
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'sort': 'relevance',
        })

        try:
            resp = requests.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params=params,
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            id_list = data.get('esearchresult', {}).get('idlist', [])
            return id_list
        except requests.RequestException as e:
            raise RuntimeError('PubMed search unavailable') from None

    def fetch_abstracts(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取文献摘要和元数据

        Args:
            pmids: PubMed ID列表

        Returns:
            文献信息列表，每个包含标题、摘要、作者、日期等
        """
        if not pmids:
            return []

        results = []

        # 分批处理 (每次最多50个)
        batch_size = 50
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]

            # E-fetch
            params = self._build_params({
                'db': 'pubmed',
                'id': ','.join(batch),
                'retmode': 'xml',
                'rettype': 'abstract',
            })

            try:
                resp = requests.get(
                    f"{self.BASE_URL}/efetch.fcgi",
                    params=params,
                    timeout=60
                )
                resp.raise_for_status()
                articles = self._parse_efetch_xml(resp.text)
                results.extend(articles)
                time.sleep(0.35)  # NCBI rate limiting (3/sec without API key)
            except requests.RequestException as e:
                raise RuntimeError('PubMed abstract fetch unavailable') from None

        return results

    def _parse_efetch_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """解析efetch返回的XML"""
        articles = []
        soup = BeautifulSoup(xml_text, 'xml')

        for article in soup.find_all('PubmedArticle'):
            try:
                info = self._extract_article_info(article)
                articles.append(info)
            except Exception as e:
                print(f"[PubMed] Parse error: {e}")
                continue

        return articles

    def _extract_article_info(self, article) -> Dict[str, Any]:
        """从XML节点提取单篇文章信息"""
        medline = article.find('MedlineCitation')
        article_node = medline.find('Article') if medline else None

        if not article_node:
            return {}

        # PMID
        pmid = medline.find('PMID').text if medline.find('PMID') else ''

        # 标题
        title_node = article_node.find('ArticleTitle')
        title = title_node.text if title_node else 'No Title Available'

        # 摘要
        abstract_parts = []
        abstract_node = article_node.find('Abstract')
        if abstract_node:
            for text_node in abstract_node.find_all('AbstractText'):
                label = text_node.get('Label', '')
                content = text_node.text if text_node.text else ''
                if label:
                    abstract_parts.append(f"[{label}] {content}")
                else:
                    abstract_parts.append(content)
        abstract = '\n'.join(abstract_parts)

        # 作者
        authors = []
        author_list = article_node.find('AuthorList')
        if author_list:
            for author in author_list.find_all('Author'):
                last = author.find('LastName')
                fore = author.find('ForeName')
                if last:
                    name = last.text
                    if fore:
                        name = f"{fore.text} {name}"
                    authors.append(name)

        # 发表日期
        pub_date = ''
        journal = article_node.find('Journal')
        if journal:
            pub_date_node = journal.find('JournalIssue').find('PubDate') if journal.find('JournalIssue') else None
            if pub_date_node:
                year = pub_date_node.find('Year')
                month = pub_date_node.find('Month')
                day = pub_date_node.find('Day')
                parts = []
                if year: parts.append(year.text)
                if month: parts.append(month.text)
                if day: parts.append(day.text)
                pub_date = ' '.join(parts)

            # 期刊名
            journal_title_node = journal.find('Title')
            journal_name = journal_title_node.text if journal_title_node else ''

            # DOI
            doi = ''
            for eid in article_node.find_all('ELocationID'):
                if eid.get('EIdType') == 'doi':
                    doi = eid.text
                    break

            # 关键词
            keywords = []
            keyword_list = medline.find('KeywordList')
            if keyword_list:
                for kw in keyword_list.find_all('Keyword'):
                    if kw.text:
                        keywords.append(kw.text)

            return {
                'source': 'PubMed',
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'date': parse_pubmed_date(pub_date),
                'year': pub_date.split()[0] if pub_date else '',
                'journal': journal_name,
                'doi': doi,
                'keywords': keywords,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }

    def search_and_fetch(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        一站式搜索并获取文献详情

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            完整的文献信息列表
        """
        pmids = self.search(query, max_results)
        if not pmids:
            return []
        return self.fetch_abstracts(pmids)

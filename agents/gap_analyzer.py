"""
研究空白与前沿探测智能体
Research Gap & Frontier Detection Agent

功能：
1. 热点分析：识别当前研究热点
2. 趋势分析：追踪研究方向演变
3. 空白识别：探测潜在研究空白
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from tools.pubmed_tool import PubMedTool
from tools.arxiv_tool import ArxivTool
from tools.llm_tool import LLMTool


@dataclass
class GapAnalysisResult:
    """空白分析结果数据结构"""
    topic: str
    hotspots: str = ""
    trends: str = ""
    gaps: str = ""
    hot_keywords: List[str] = field(default_factory=list)
    emerging_keywords: List[str] = field(default_factory=list)
    raw_articles: List[Dict[str, Any]] = field(default_factory=list)


class GapAnalyzer:
    """
    研究空白与前沿探测智能体

    功能：
    - 基于跨库文献检索分析研究热点
    - 识别新兴趋势和前沿方向
    - 探测"研究空白"领域
    - 提供未来研究建议
    """

    def __init__(self):
        self.pubmed = PubMedTool()
        self.arxiv = ArxivTool()
        self.llm = LLMTool()

    def analyze(self, topic: str, deep_search: bool = True) -> GapAnalysisResult:
        """
        执行完整的研究空白分析

        Args:
            topic: 研究主题
            deep_search: 是否进行深度检索（更多文献）

        Returns:
            GapAnalysisResult对象
        """
        # Step 1: 跨库检索相关文献
        pubmed_max = 50 if deep_search else 25
        arxiv_max = 30 if deep_search else 15

        all_articles = []

        try:
            pubmed_results = self.pubmed.search_and_fetch(topic, pubmed_max)
            all_articles.extend(pubmed_results)
        except Exception as e:
            print(f"[GapAnalyzer] PubMed error: {e}")

        try:
            arxiv_results = self.arxiv.search(topic, arxiv_max)
            all_articles.extend(arxiv_results)
        except Exception as e:
            print(f"[GapAnalyzer] arXiv error: {e}")

        # 排序和去重
        all_articles.sort(key=lambda x: x.get('year', '0'), reverse=True)

        seen = set()
        unique_articles = []
        for article in all_articles:
            normalized = ''.join(
                c for c in article.get('title', '').lower().strip() if c.isalnum()
            )
            if normalized and normalized[:60] not in seen:
                seen.add(normalized[:60])
                unique_articles.append(article)

        if not unique_articles:
            return GapAnalysisResult(
                topic=topic,
                hotspots="未检索到足够文献进行分析。",
                trends="数据不足。",
                gaps="无法确定研究空白。",
            )

        # Step 2: 使用LLM分析趋势和空白
        analysis = self.llm.analyze_trends_and_gaps(topic, unique_articles)

        return GapAnalysisResult(
            topic=topic,
            hotspots=analysis.get('hotspots', ''),
            trends=analysis.get('trends', ''),
            gaps=analysis.get('gaps', ''),
            hot_keywords=analysis.get('keywords_hot', []),
            emerging_keywords=analysis.get('keywords_emerging', []),
            raw_articles=unique_articles,
        )

    def analyze_hotspots_only(self, topic: str) -> Dict[str, Any]:
        """
        仅执行热点分析（轻量级）

        Args:
            topic: 研究主题

        Returns:
            热点分析结果
        """
        result = self.analyze(topic, deep_search=False)
        return {
            'topic': topic,
            'hotspots': result.hotspots,
            'hot_keywords': result.hot_keywords,
            'emerging_keywords': result.emerging_keywords,
        }

    def detect_gaps_only(self, topic: str) -> Dict[str, Any]:
        """
        仅执行空白探测（深度分析）

        Args:
            topic: 研究主题

        Returns:
            空白探测结果
        """
        result = self.analyze(topic, deep_search=True)
        return {
            'topic': topic,
            'gaps': result.gaps,
            'trends': result.trends,
            'suggestions': self._extract_suggestions(result.gaps),
        }

    def _extract_suggestions(self, gaps_text: str) -> List[str]:
        """从空白分析文本中提取具体的未来研究方向建议"""
        suggestions = []
        lines = gaps_text.split('\n')
        for line in lines:
            stripped = line.strip()
            # 寻找建议性语句
            indicators = ['建议', '可以', '方向', '空白', 'gap', 'future', 'opportunity',
                          '值得', '尚需', '需要进一步', '尚未', '有待']
            if any(ind in stripped.lower() for ind in indicators):
                # 清理格式
                cleaned = stripped.lstrip('0123456789.、-•· \t')
                if len(cleaned) > 10:
                    suggestions.append(cleaned)
        return suggestions[:10]  # 最多10条

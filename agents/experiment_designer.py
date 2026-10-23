"""
实验方案设计建议智能体
Experiment Design Agent

功能：
1. 实验设计辅助：生成初步的实验设计方案
2. 方法推荐：推荐合适的实验方法和数据分析技术
3. 技术路线规划
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from tools.pubmed_tool import PubMedTool
from tools.arxiv_tool import ArxivTool
from tools.llm_tool import LLMTool


@dataclass
class ExperimentDesign:
    """实验设计结果数据结构"""
    research_question: str
    full_design: str = ""
    method_recommendations: str = ""
    referenced_articles: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.referenced_articles is None:
            self.referenced_articles = []


class ExperimentDesigner:
    """
    实验方案设计建议智能体

    功能：
    - 针对科学问题生成完整实验方案
    - 推荐实验方法和数据分析技术
    - 基于领域文献提供方法学参考
    """

    def __init__(self):
        self.pubmed = PubMedTool()
        self.arxiv = ArxivTool()
        self.llm = LLMTool()

    def design_experiment(self, research_question: str,
                          search_methods: bool = True) -> ExperimentDesign:
        """
        设计完整实验方案

        Args:
            research_question: 研究问题
            search_methods: 是否先检索相关方法论文献

        Returns:
            ExperimentDesign对象
        """
        referenced_articles = []

        # 可选：检索相关方法论文献作为参考
        if search_methods:
            method_query = f"({research_question}) AND (method OR protocol OR technique)"
            try:
                pubmed_results = self.pubmed.search_and_fetch(method_query, 10)
                arxiv_results = self.arxiv.search(method_query, 5)
                referenced_articles = pubmed_results + arxiv_results
            except Exception as e:
                print(f"[ExperimentDesigner] Method search error: {e}")

        # 生成完整实验设计
        full_design = self.llm.design_experiment(
            research_question,
            referenced_articles if referenced_articles else None
        )

        return ExperimentDesign(
            research_question=research_question,
            full_design=full_design,
            referenced_articles=referenced_articles,
        )

    def recommend_methods(self, research_question: str) -> str:
        """
        推荐实验方法和数据分析技术

        Args:
            research_question: 研究问题

        Returns:
            方法推荐 (Markdown格式)
        """
        return self.llm.recommend_methods(research_question)

    def design_with_recommendations(self, research_question: str) -> ExperimentDesign:
        """
        一站式：方法推荐 + 完整实验设计

        Args:
            research_question: 研究问题

        Returns:
            ExperimentDesign对象（包含方法推荐和完整设计）
        """
        # 先获取方法推荐
        method_recommendations = self.recommend_methods(research_question)

        # 再设计完整实验方案
        result = self.design_experiment(research_question, search_methods=True)
        result.method_recommendations = method_recommendations

        return result

    def validate_design(self, design_text: str) -> Dict[str, Any]:
        """
        验证实验设计的关键要素是否齐全

        Args:
            design_text: 实验设计文本

        Returns:
            验证结果字典
        """
        checks = {
            'hypothesis': '假设' in design_text or 'hypothesis' in design_text.lower(),
            'control_group': '对照' in design_text or 'control' in design_text.lower(),
            'sample_size': '样本' in design_text or 'sample size' in design_text.lower(),
            'variables': '变量' in design_text or 'variable' in design_text.lower(),
            'statistical_analysis': '统计' in design_text or 'statistical' in design_text.lower(),
            'expected_results': '预期' in design_text or 'expected' in design_text.lower(),
            'limitations': '局限' in design_text or 'limitation' in design_text.lower(),
        }

        completeness = sum(1 for v in checks.values() if v) / len(checks) * 100

        return {
            'checks': checks,
            'completeness': f"{completeness:.0f}%",
            'missing': [k for k, v in checks.items() if not v],
        }

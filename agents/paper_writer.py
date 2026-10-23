"""
论文写作辅助智能体
Paper Writing Assistant Agent

功能：
1. 章节草稿生成：引言、方法、结果、讨论、摘要
2. 格式规范：支持多种期刊风格
3. 参考文献管理
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from tools.llm_tool import LLMTool
from config import JOURNAL_STYLES


@dataclass
class PaperDraft:
    """论文草稿数据结构"""
    title: str = ""
    abstract: str = ""
    introduction: str = ""
    methods: str = ""
    results: str = ""
    discussion: str = ""
    references: List[str] = field(default_factory=list)
    target_journal_style: str = "通用学术规范"


class PaperWriter:
    """
    论文写作辅助智能体

    功能：
    - 根据实验数据和笔记生成各章节草稿
    - 支持多种期���风格（Nature, Science, Cell等）
    - 格式规范检查
    """

    def __init__(self):
        self.llm = LLMTool()
        self.available_styles = JOURNAL_STYLES

    def generate_section(self, section: str,
                         context: Dict[str, Any],
                         style: str = "通用学术规范") -> str:
        """
        生成单个章节的草稿

        Args:
            section: 章节名称
                - 'abstract': 摘要
                - 'introduction': 引言
                - 'methods': 方法
                - 'results': 结果
                - 'discussion': 讨论
            context: 写作上下文，可包含以下键：
                - 'title': 论文标题
                - 'research_question': 研究问题
                - 'background': 背景信息
                - 'experimental_data': 实验数据
                - 'methods_description': 方法描述
                - 'results_data': 结果数据
                - 'notes': 笔记/要点
                - 'references': 参考文献列表
            style: 目标期刊风格

        Returns:
            生成的章节草稿 (Markdown格式)
        """
        valid_sections = ['abstract', 'introduction', 'methods', 'results', 'discussion']
        if section not in valid_sections:
            raise ValueError(f"无效的章节: {section}。可选: {valid_sections}")

        return self.llm.generate_paper_draft(section, context, style)

    def generate_full_paper(self, context: Dict[str, Any],
                            style: str = "通用学术规范") -> PaperDraft:
        """
        生成完整论文草稿（所有章节）

        Args:
            context: 写作上下文
            style: 目标期刊风格

        Returns:
            PaperDraft对象，包含所有章节
        """
        title = context.get('title', 'Untitled')

        draft = PaperDraft(
            title=title,
            target_journal_style=style,
        )

        # 按顺序生成各章节
        print(f"[PaperWriter] Generating abstract...")
        draft.abstract = self.generate_section('abstract', context, style)

        print(f"[PaperWriter] Generating introduction...")
        draft.introduction = self.generate_section('introduction', context, style)

        print(f"[PaperWriter] Generating methods...")
        draft.methods = self.generate_section('methods', context, style)

        print(f"[PaperWriter] Generating results...")
        draft.results = self.generate_section('results', context, style)

        print(f"[PaperWriter] Generating discussion...")
        draft.discussion = self.generate_section('discussion', context, style)

        # References
        if 'references' in context:
            refs = context['references']
            if isinstance(refs, list):
                draft.references = refs
            elif isinstance(refs, str):
                draft.references = [refs]

        return draft

    def get_writing_tips(self, section: str, style: str = "通用学术规范") -> str:
        """
        获取特定章节的写作提示

        Args:
            section: 章节名称
            style: 期刊风格

        Returns:
            写作提示
        """
        tips = {
            'abstract': {
                '通用': (
                    "摘要写作要点：\n"
                    "- 控制在200-300字\n"
                    "- 结构：背景→目的→方法→结果→结论\n"
                    "- 避免引用文献\n"
                    "- 突出创新点和意义"
                ),
                'Nature': (
                    "Nature摘要要点：\n"
                    "- 约150字\n"
                    "- 单段格式\n"
                    "- 必须包含研究的基本原理、主要结果和广泛意义\n"
                    "- 避免专业术语过多"
                ),
            },
            'introduction': {
                '通用': (
                    "引言写作要点：\n"
                    "- 漏斗式结构：从宽到窄\n"
                    "- 第1段：领域背景\n"
                    "- 第2-3段：文献回顾与知识空白\n"
                    "- 最后一段：研究目的与假设\n"
                    "- 合理引用关键文献"
                ),
            },
            'methods': {
                '通用': (
                    "方法写作要点：\n"
                    "- 使用被动语态和过去时\n"
                    "- 提供足够细节以确保可重复\n"
                    "- 分小节：实验设计、材料、数据采集、统计分析\n"
                    "- 引用标准方法时简要说明即可"
                ),
            },
            'results': {
                '通用': (
                    "结果写作要点：\n"
                    "- 客观呈现，不讨论\n"
                    "- 图文结合（Fig. 1, Table 1）\n"
                    "- 报告统计量（p值、效应量等）\n"
                    "- 按逻辑顺序组织"
                ),
            },
            'discussion': {
                '通用': (
                    "讨论写作要点：\n"
                    "- 首段：总结关键发现\n"
                    "- 中段：与文献对比、解释机制\n"
                    "- 末段：局限性 + 未来方向 + 结论\n"
                    "- 不要重复结果部分的数据"
                ),
            },
        }

        section_tips = tips.get(section, {})
        return section_tips.get(style, section_tips.get('通用', '暂无该章节的写作提示。'))

    def format_check(self, text: str, style: str = "通用学术规范") -> Dict[str, Any]:
        """
        检查文本格式是否符合学术规范

        Args:
            text: 待检查的文本
            style: 目标风格

        Returns:
            格式检查结果
        """
        checks = {
            'has_citations': bool('[1]' in text or '(1)' in text or 'et al.' in text.lower()),
            'word_count': len(text),
            'has_sections': bool('引言' in text or 'Introduction' in text or '方法' in text),
            'no_contractions': "don't" not in text.lower() and "can't" not in text.lower(),
            'formal_tone': self._check_formal_tone(text),
        }

        return {
            'checks': checks,
            'style': style,
            'score': sum(1 for v in checks.values() if v) / len(checks) * 100,
        }

    def _check_formal_tone(self, text: str) -> bool:
        """简单检查是否使用正式语气（检查非正式词汇）"""
        informal_words = ['really', 'very', 'totally', 'absolutely', 'huge',
                          'amazing', 'awesome', 'great', 'bad', 'good',
                          '好多', '非常', '很', '超级']
        text_lower = text.lower()
        for word in informal_words:
            if word in text_lower:
                return False
        return True

"""
LLM集成工具
支持DeepSeek、Anthropic Claude和OpenAI三种后端
提供文献分析、综述生成、实验设计、论文写作等智能功能
"""

import json
import re
from typing import List, Dict, Any, Optional

from config import (
    LLM_PROVIDER,
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    DEEPSEEK_BASE_URL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)


class LLMTool:
    """LLM调用统一接口，支持 DeepSeek / Claude / OpenAI"""

    def __init__(self, provider: str = None):
        self.provider = provider or LLM_PROVIDER

        if self.provider == "deepseek":
            if not DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY not configured")
            from openai import OpenAI
            self.client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=DEEPSEEK_BASE_URL,
            )
            self.model = DEEPSEEK_MODEL

        elif self.provider == "anthropic":
            if not ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            import anthropic
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            self.model = ANTHROPIC_MODEL

        elif self.provider == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            from openai import OpenAI
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model = OPENAI_MODEL

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def chat(self, messages: List[Dict[str, str]], system: str = None,
             temperature: float = 0.3, max_tokens: int = 4096) -> str:
        """
        通用LLM调用

        Args:
            messages: 聊天消息列表
            system: 系统提示
            temperature: 温度参数
            max_tokens: 最大输出token数

        Returns:
            LLM响应文本
        """
        try:
            if self.provider == "anthropic":
                return self._chat_anthropic(messages, system, temperature, max_tokens)
            else:
                # DeepSeek 和 OpenAI 都使用 OpenAI 兼容接口
                return self._chat_openai_compatible(messages, system, temperature, max_tokens)
        except Exception as e:
            raise RuntimeError('模型调用失败，请检查本地配置或稍后重试。') from None

    def _chat_openai_compatible(self, messages: List[Dict[str, str]], system: str,
                                temperature: float, max_tokens: int) -> str:
        """OpenAI 兼容接口 (DeepSeek / OpenAI)"""
        full_messages = []
        if system:
            full_messages.append({'role': 'system', 'content': system})
        full_messages.extend(messages)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    def _chat_anthropic(self, messages: List[Dict[str, str]], system: str,
                        temperature: float, max_tokens: int) -> str:
        """Anthropic Claude API调用"""
        user_messages = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system' and not system:
                system = content
            else:
                user_messages.append({
                    'role': 'user',
                    'content': [{'type': 'text', 'text': content}],
                })

        if not user_messages:
            user_messages = [{'role': 'user', 'content': [{'type': 'text', 'text': 'Please proceed.'}]}]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system or '',
            messages=user_messages,
        )

        text_blocks = [block.text for block in response.content if block.type == 'text']
        return '\n'.join(text_blocks)

    # ================================================================
    # 专用方法 - 为各个智能体模块提供特定功能
    # ================================================================

    def generate_structured_review(self, topic: str, articles: List[Dict[str, Any]]) -> str:
        """
        生成结构化文献综述

        Args:
            topic: 研究主题
            articles: 文献列表

        Returns:
            结构化的文献综述 (Markdown格式)
        """
        lit_text = self._format_articles_for_prompt(articles, max_articles=30)

        system_prompt = """你是一位资深的科学研究方法论专家。请根据提供的文献列表，生成一份结构化的文献综述。

要求：
1. 使用中文撰写（保留英文专业术语）
2. 结构清晰，包含以下部分：
   - **研究背景与意义**：该领域的研究价值
   - **主要研究方向**：归纳当前主要的几个研究方向
   - **关键发现与方法论**：总结重要发现和主流研究方法
   - **代表性文献**：列举3-5篇最具代表性的文献及其贡献
   - **研究趋势**：分析近年来的发展趋势
3. 在综述末尾提供完整的参考文献列表
4. 标注引用来源，便于追踪原始文献
5. 语言学术化、专业化"""

        user_prompt = f"""研究主题：{topic}

检索到的相关文献（共{len(articles)}篇）：

{lit_text}

请基于以上文献，生成一份完整的结构化文献综述。"""

        return self.chat(
            messages=[{'role': 'user', 'content': user_prompt}],
            system=system_prompt,
            temperature=0.3,
            max_tokens=4096,
        )

    def generate_abstract_summary(self, topic: str, articles: List[Dict[str, Any]]) -> str:
        """
        生成简明摘要

        Args:
            topic: 研究主题
            articles: 文献列表

        Returns:
            简明摘要
        """
        lit_text = self._format_articles_for_prompt(articles, max_articles=20)

        system_prompt = """你是一位科学传播专家。请根据提供的文献，生成一份简明的研究主题摘要。

要求：
1. 使用中文撰写（保留英文专业术语）
2. 控制在500-800字
3. 包含：核心研究问题、主要发现、关键方法、知识空白
4. 适合快速了解该领域的研究现状
5. 语言通俗但不失专业性"""

        user_prompt = f"""研究主题：{topic}

相关文献摘要（共{len(articles)}篇）：

{lit_text}

请生成一份简明摘要（500-800字），帮助快速了解该领域的研究现状。"""

        return self.chat(
            messages=[{'role': 'user', 'content': user_prompt}],
            system=system_prompt,
            temperature=0.3,
            max_tokens=2048,
        )

    def analyze_trends_and_gaps(self, topic: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析研究热点、趋势和研究空白

        Args:
            topic: 研究主题
            articles: 文献列表

        Returns:
            包含热点分析、趋势分析和空白识别的字典
        """
        lit_text = self._format_articles_for_prompt(articles, max_articles=40)

        system_prompt = """你是一位顶级的科学计量学和科研战略专家。请基于提供的文献列表，进行深入、全面的研究领域分析。

你必须输出一个有效的JSON对象，格式如下（注意：字段值必须是你实际撰写的分析内容，不能是占位符）：
{
  "hotspots": "在这里写你的热点分析内容（不少于800字）...",
  "trends": "在这里写你的趋势分析内容（不少于800字）...",
  "gaps": "在这里写你的空白分析内容（不少于800字）...",
  "keywords_hot": ["关键词1", "关键词2", "关键词3", ...],
  "keywords_emerging": ["新兴词1", "新兴词2", "新兴词3", ...]
}

=== 分析要求 ===

【热点分析】(不少于800字)：
1. 基于文献内容，识别3-5个核心研究热点主题，每个主题用一段详细阐述
2. 说明每个热点为什么热（解决的问题、应用的广度、学术界关注度）
3. 引用至少3篇具体文献作为每个热点的依据（用文献编号如[1][2]）
4. 分析不同热点之间的关联和交叉
5. 指出这些热点的代表性工作和技术路线

【趋势与前沿】(不少于800字)：
1. 按时间线分析研究方向如何演变（从早期→现在→未来）
2. 识别2-3个正在快速兴起的新方向
3. 分析驱动这些趋势的技术因素（新算法、新硬件、新数据等）
4. 预判未来2-3年可能的发展方向
5. 结合文献中的实验结论支持你的判断

【研究空白】(不少于800字)：
1. 识别3-5个现有研究未充分覆盖的领域
2. 分析每个空白的成因（技术限制、数据缺乏、理论不足等）
3. 说明填补这些空白的潜在价值和意义
4. 为每个空白提出具体的研究方向建议
5. 指出入门该空白的可行路径

重要提醒：
- 全部使用中文撰写（保留英文专业术语）
- 每个分析都要引用具体文献编号作为依据，如[3][7][15]
- 观点要有深度，给出具体的、可操作的洞察
- 避免泛泛而谈，尽量具体到方法、数据、性能指标
- JSON字符串中的双引号必须用反斜杠转义 \"
- 务必输出完整的JSON，不要省略任何字段"""

        user_prompt = f"""研究主题：{topic}

检索到的相关文献（共{len(articles)}篇）：

{lit_text}

请基于以上文献，进行深入、详细的研究热点、趋势和空白分析。每个部分不少于800字，引用文献编号。严格输出JSON格式。"""

        response = self.chat(
            messages=[{'role': 'user', 'content': user_prompt}],
            system=system_prompt,
            temperature=0.4,
            max_tokens=8192,
        )

        # 调试：打印原始响应的前200字符
        print(f"[LLM] analyze_trends_and_gaps response length: {len(response)}")
        print(f"[LLM] Response preview: {response[:300]}...")

        # 多种策略解析JSON
        parsed = self._parse_json_response(response)

        if parsed:
            return parsed

        # 最终回退：按关键词分段提取
        print("[LLM] JSON parsing failed, falling back to section extraction")
        return self._fallback_extract_sections(response)

    def design_experiment(self, research_question: str, articles: List[Dict[str, Any]] = None) -> str:
        """
        辅助设计实验方案

        Args:
            research_question: 研究问题
            articles: 可选的参考文献列表

        Returns:
            实验设计方案 (Markdown格式)
        """
        context = ""
        if articles:
            context = "\n\n可参考的文献：\n" + self._format_articles_for_prompt(articles, max_articles=10)

        system_prompt = """你是一位实验科学方法论专家。请针对给定的研究问题，设计一套完整的实验方案。

要求：
1. 使用中文撰写（保留英文专业术语）
2. 包含以下完整部分：
   **一、研究假设**：明确提出待验证的假设
   **二、实验设计**
   - 实验分组（对照组、实验组设计）
   - 样本量估算（需说明依据）
   - 变量控制（自变量、因变量、控制变量）
   **三、技术路线**
   - 详细实验步骤（可操作的步骤）
   - 关键技术和方法
   - 数据采集方案
   **四、数据分析方案**
   - 统计分析方法
   - 数据可视化建议
   - 结果解读框架
   **五、预期结果与讨论**
   - 可能的实验结果
   - 结果的意义
   - 潜在问题与应对策略
3. 推荐合适的具体实验方法和数据分析技术
4. 考虑实验的可行性和可重复性"""

        user_prompt = f"研究问题：{research_question}{context}\n\n请设计一套完整的实验方案。"

        return self.chat(
            messages=[{'role': 'user', 'content': user_prompt}],
            system=system_prompt,
            temperature=0.3,
            max_tokens=4096,
        )

    def recommend_methods(self, research_question: str) -> str:
        """
        推荐实验方法和数据分析技术

        Args:
            research_question: 研究问题

        Returns:
            方法推荐 (Markdown格式)
        """
        system_prompt = """你是一位跨学科研究方法专家。请针对给定的研究问题，推荐最合适的实验方法和数据分析技术。

要求：
1. 使用中文撰写（保留英文专业术语）
2. 推荐2-3种主要的实验方法，对每种方法说明：
   - 方法名称和原理
   - 适用性分析（为什么适合该问题）
   - 优缺点
   - 所需设备和条件
   - 预期的产出数据类型
3. 推荐相应的数据分析技术：
   - 统计方法
   - 机器学习方法（如适用）
   - 可视化方式
4. 给出首选推荐和备选方案"""

        user_prompt = f"研究问题：{research_question}\n\n请推荐合适的实验方法和数据分析技术。"

        return self.chat(
            messages=[{'role': 'user', 'content': user_prompt}],
            system=system_prompt,
            temperature=0.3,
            max_tokens=3072,
        )

    def generate_paper_draft(self, section: str, context: Dict[str, Any], style: str = "通用学术规范") -> str:
        """
        生成论文章节草稿

        Args:
            section: 章节名称 (introduction/methods/results/discussion/abstract)
            context: 包含实验数据、笔记、参考文献等信息
            style: 目标期刊风格

        Returns:
            生成的章节草稿 (Markdown格式)
        """
        section_prompts = {
            'introduction': (
                "你是一位学术写作专家。请基于提供的信息，撰写论文的【引言/Introduction】章节。\n\n"
                "要求：\n"
                "1. 从宏观背景逐步聚焦到具体研究问题（漏斗式结构）\n"
                "2. 系统回顾相关文献，指出知识空白\n"
                "3. 明确提出研究目的和假设\n"
                "4. 简要说明研究意义和创新点\n"
                f"5. 符合{style}的写作风格和格式要求\n"
                "6. 包含适当的引用标注"
            ),
            'methods': (
                "你是一位学术写作专家。请基于提供的信息，撰写论文的【方法/Methods】章节。\n\n"
                "要求：\n"
                "1. 详细描述实验设计、材料和步骤\n"
                "2. 说明数据采集和分析方法\n"
                "3. 确保实验可重复性（提供足够细节）\n"
                "4. 说明统计分析方法\n"
                f"5. 符合{style}的写作风格和格式要求\n"
                "6. 使用被动语态和过去时"
            ),
            'results': (
                "你是一位学术写作专家。请基于提供的信息，撰写论文的【结果/Results】章节。\n\n"
                "要求：\n"
                "1. 客观呈现实验结果和数据\n"
                "2. 合理使用图表引用（标注Fig.1, Table 1等）\n"
                "3. 突出关键发现，但不进行深入讨论\n"
                "4. 使用适当的统计表述\n"
                f"5. 符合{style}的写作风格和格式要求"
            ),
            'discussion': (
                "你是一位学术写作专家。请基于提供的信息，撰写论文的【讨论/Discussion】章节。\n\n"
                "要求：\n"
                "1. 总结关键发现\n"
                "2. 与已有文献进行对比讨论\n"
                "3. 解释结果的意义和潜在机制\n"
                "4. 诚实讨论研究局限性\n"
                "5. 提出未来研究方向\n"
                f"6. 符合{style}的写作风格和格式要求"
            ),
            'abstract': (
                "你是一位学术写作专家。请基于提供的信息，撰写论文的【摘要/Abstract】。\n\n"
                "要求：\n"
                "1. 控制在250-300字\n"
                "2. 包含：背景(1句)、目的(1句)、方法(2-3句)、结果(2-3句)、结论(1-2句)\n"
                "3. 突出研究的创新性和意义\n"
                f"4. 符合{style}的摘要格式要求"
            ),
        }

        system_prompt = section_prompts.get(
            section,
            f"你是一位学术写作专家。请撰写论文的【{section}】章节，符合{style}的风格要求。"
        )

        context_parts = []
        for key, value in context.items():
            if isinstance(value, list):
                value = '\n'.join(str(v) for v in value[:10])
            context_parts.append(f"【{key}】\n{value}")
        context_text = '\n\n'.join(context_parts)

        user_prompt = f"""以下是撰写所需的信息：

{context_text}

请基于以上信息，撰写{section}章节的草稿。"""

        return self.chat(
            messages=[{'role': 'user', 'content': user_prompt}],
            system=system_prompt,
            temperature=0.4,
            max_tokens=4096,
        )

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """多种策略尝试解析LLM返回的JSON"""
        import re

        strategies = [
            # 策略1: 提取 ```json ... ``` 代码块
            (r'```json\s*([\s\S]*?)\s*```', 1),
            # 策略2: 提取 ``` ... ``` 代码块
            (r'```\s*([\s\S]*?)\s*```', 1),
            # 策略3: 匹配最外层大括号（非贪婪嵌套）
            (r'\{[\s\S]*\}', 0),
        ]

        for pattern, group in strategies:
            match = re.search(pattern, response)
            if match:
                json_str = match.group(group) if group else match.group(0)
                try:
                    result = json.loads(json_str)
                    # 验证必要字段存在
                    if all(k in result for k in ['hotspots', 'trends', 'gaps']):
                        print(f"[LLM] JSON parsed successfully via pattern: {pattern[:30]}...")
                        return {
                            'hotspots': result.get('hotspots', ''),
                            'trends': result.get('trends', ''),
                            'gaps': result.get('gaps', ''),
                            'keywords_hot': result.get('keywords_hot', []),
                            'keywords_emerging': result.get('keywords_emerging', []),
                        }
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"[LLM] JSON parse failed for pattern '{pattern[:30]}...': {e}")
                    continue

        return None

    def _fallback_extract_sections(self, response: str) -> Dict[str, Any]:
        """回退方案：从纯文本中按标题分段提取内容"""
        import re

        keywords_hot = []
        keywords_emerging = []

        # 提取关键词
        hot_match = re.search(r'"keywords_hot"\s*:\s*\[(.*?)\]', response, re.DOTALL)
        if hot_match:
            keywords_hot = re.findall(r'"([^"]+)"', hot_match.group(1))

        emerg_match = re.search(r'"keywords_emerging"\s*:\s*\[(.*?)\]', response, re.DOTALL)
        if emerg_match:
            keywords_emerging = re.findall(r'"([^"]+)"', emerg_match.group(1))

        # 按中文标题分段
        hotspots = ""
        trends = ""
        gaps = ""

        # 尝试按 "热点" "趋势" "空白" 分段
        sections = re.split(r'(?:###?\s*)?(?:研究)?热点[分析：:]', response)
        if len(sections) > 1:
            rest = sections[1]
            # 再分趋势
            trend_split = re.split(r'(?:###?\s*)?(?:研究)?趋势[分析：:]', rest)
            if len(trend_split) > 1:
                hotspots = trend_split[0].strip()
                rest2 = trend_split[1]
                gap_split = re.split(r'(?:###?\s*)?(?:研究)?空白[分析：:]', rest2)
                if len(gap_split) > 1:
                    trends = gap_split[0].strip()
                    gaps = gap_split[1].strip()
                else:
                    trends = rest2.strip()

        # 如果分段失败，整体三等分
        if not hotspots and not trends and not gaps and response:
            third = len(response) // 3
            hotspots = response[:third].strip()
            trends = response[third:2*third].strip()
            gaps = response[2*third:].strip()

        return {
            'hotspots': hotspots,
            'trends': trends,
            'gaps': gaps,
            'keywords_hot': keywords_hot,
            'keywords_emerging': keywords_emerging,
        }

    def _format_articles_for_prompt(self, articles: List[Dict[str, Any]], max_articles: int = 30) -> str:
        """将文献列表格式化为LLM prompt可用的文本"""
        formatted = []
        for i, article in enumerate(articles[:max_articles], 1):
            title = article.get('title', 'No Title')
            authors = ', '.join(article.get('authors', [])[:5])
            if len(article.get('authors', [])) > 5:
                authors += ' et al.'
            year = article.get('year', '')
            source = article.get('source', '')
            abstract = article.get('abstract', '')[:800]
            url = article.get('url', '')

            text = f"[{i}] {title}\n"
            text += f"    作者: {authors}\n"
            text += f"    年份: {year} | 来源: {source}\n"
            text += f"    摘要: {abstract}\n"
            if url:
                text += f"    链接: {url}\n"
            formatted.append(text)

        return '\n' + '\n'.join(formatted)

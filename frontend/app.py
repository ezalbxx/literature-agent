"""
AI科学文献研究智能体 - 前端应用 (前后端分离版)
Streamlit Web Interface → 调用 FastAPI 后端

四大功能模块：
1. 跨库文献智能检索与摘要
2. 研究空白与前沿探测
3. 实验方案设计建议
4. 论文写作辅助
"""

import streamlit as st
import time
from datetime import datetime

from api_client import APIClient, APIError
from config import APP_NAME, APP_VERSION, APP_DESCRIPTION, JOURNAL_STYLES

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS样式
# ============================================================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 50%, #4a90d9 100%);
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        font-size: 2.2rem;
        margin: 0;
    }
    .main-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1rem;
        margin-top: 0.3rem;
    }
    .result-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-left: 4px solid #2d6a9f;
    }
    .result-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .article-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stat-box {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
    }
    .stat-box .number {
        font-size: 2rem;
        font-weight: bold;
    }
    .stat-box .label {
        font-size: 0.85rem;
        opacity: 0.9;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        padding: 0.5rem 1.5rem;
    }
    .stTextArea>div>div>textarea {
        border-radius: 8px;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 初始化 Session State
# ============================================================
def init_session():
    """初始化session state"""
    defaults = {
        'search_results': None,
        'search_query': '',
        'gap_analysis': None,
        'experiment_design': None,
        'paper_draft': None,
        'current_articles': [],
        'search_history': [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.title("🔬 导航菜单")

    # 后端健康检查
    try:
        health = APIClient.health()
        st.success(f"🟢 后端服务正常 | {health['llm_provider']} v{health['version']}")
    except Exception:
        st.error("🔴 后端连接失败！请启动后端服务")

    st.divider()

    # 功能选择
    function = st.radio(
        "选择功能模块",
        [
            "🔗 研究工作台",
            "📚 1. 跨库文献检索与摘要",
            "🔍 2. 研究空白与前沿探测",
            "🧪 3. 实验方案设计建议",
            "✍️ 4. 论文写作辅助",
            "🧠 5. PDF 文献问答",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.caption(f"🤖 LLM: DeepSeek-Chat")
    st.caption(f"📊 数据库: PubMed + arXiv")
    st.caption(f"🔄 版本: v{APP_VERSION}")

    st.divider()

    # 已保存结果
    st.divider()
    st.subheader("📂 已保存结果")

    if st.button("🔄 刷新列表", use_container_width=True):
        st.rerun()

    try:
        saved = APIClient.history_list()
        items = saved.get('items', [])
        if items:
            for item in items:
                module_icons = {
                    'literature': '📚', 'gap': '🔍',
                    'experiment': '🧪', 'paper': '✍️',
                }
                icon = module_icons.get(item['module'], '📄')
                ts = item['timestamp'][:16].replace('T', ' ')
                label = f"{icon} {item['title'][:30]} ({ts})"

                col_a, col_b = st.columns([4, 1])
                with col_a:
                    if st.button(label, key=f"load_{item['id']}", use_container_width=True,
                                 help=item.get('preview', '')):
                        try:
                            full = APIClient.history_get(item['id'])
                            data = full['data']
                            module = full['module']
                            if module == 'literature':
                                st.session_state.search_results = data
                                st.session_state.current_articles = data.get('articles', [])
                            elif module == 'gap':
                                st.session_state.gap_analysis = data
                            elif module == 'experiment':
                                st.session_state.experiment_design = data
                            elif module == 'paper':
                                st.session_state.paper_draft = data
                            st.rerun()
                        except APIError:
                            st.error("加载失败")
                with col_b:
                    if st.button("🗑", key=f"del_{item['id']}", help="删除"):
                        try:
                            APIClient.history_delete(item['id'])
                            st.rerun()
                        except APIError:
                            pass
        else:
            st.caption("暂无保存结果")
    except Exception:
        st.caption("无法加载历史记录")

# ============================================================
# 辅助函数
# ============================================================
def show_api_error(func_name: str, e: Exception):
    """统一显示API错误"""
    st.error(f"❌ {func_name}失败: {str(e)}")

# ============================================================
# 主页面头部
# ============================================================
st.markdown(f"""
<div class="main-header">
    <h1>🔬 {APP_NAME}</h1>
    <p>{APP_DESCRIPTION}</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 模块1：跨库文献智能检索与摘要
# ============================================================
if function.startswith("📚"):
    st.header("📚 跨库文献智能检索与摘要")
    st.markdown("*支持 PubMed + arXiv 双库检索，自动生成结构化综述和简明摘要*")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        query = st.text_input(
            "研究主题 / 搜索关键词",
            placeholder="例如：CRISPR gene editing cancer therapy, 深度学习蛋白质结构预测...",
            key="lit_query",
        )
    with col2:
        pubmed_max = st.number_input("PubMed 最大结果", 5, 100, 30, 5, key="pubmed_max")
    with col3:
        arxiv_max = st.number_input("arXiv 最大结果", 5, 50, 20, 5, key="arxiv_max")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        search_btn = st.button("🔍 开始检索与分析", type="primary", use_container_width=True)

    if search_btn and query:
        with st.spinner("🔄 正在跨库检索文献与分析（可能需要30-60秒）..."):
            st.session_state.search_history.append(query)
            st.session_state.search_query = query

            try:
                result = APIClient.literature_search_and_review(query, pubmed_max, arxiv_max)
                st.session_state.search_results = result
                st.session_state.current_articles = result['articles']
                st.success("✅ 检索与分析完成！")
                # 自动保存
                try:
                    APIClient.history_save("literature", query[:50], query, result)
                except Exception:
                    pass
            except APIError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ 未知错误: {str(e)}")

    # 显示结果
    if st.session_state.search_results:
        result = st.session_state.search_results
        for warning in result.get('warnings', []):
            st.warning(warning)

        # 统计卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="stat-box">
                <div class="number">{len(result['articles'])}</div>
                <div class="label">检索文献总数</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-box">
                <div class="number">{result['total_pubmed']}</div>
                <div class="label">PubMed 文献</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-box">
                <div class="number">{result['total_arxiv']}</div>
                <div class="label">arXiv 文献</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            years = [a.get('year', '0') for a in result['articles'] if a.get('year', '').isdigit()]
            latest = max(years) if years else 'N/A'
            st.markdown(f"""
            <div class="stat-box">
                <div class="number">{latest}</div>
                <div class="label">最新年份</div>
            </div>
            """, unsafe_allow_html=True)

        # Tab切换
        tab1, tab2, tab3 = st.tabs(["📝 结构化综述", "📋 简明摘要", "📄 文献列表"])

        with tab1:
            if result['structured_review']:
                st.markdown(result['structured_review'])
            else:
                st.info("综述内容为空")

        with tab2:
            if result['abstract_summary']:
                st.markdown(result['abstract_summary'])
            else:
                st.info("摘要内容为空")

        with tab3:
            st.caption(f"共 {len(result['articles'])} 篇文献")
            for i, article in enumerate(result['articles']):
                title = article.get('title', 'No Title')
                authors_list = article.get('authors', [])
                authors_str = ', '.join(authors_list[:5]) if authors_list else 'N/A'
                with st.expander(f"[{i+1}] {title[:120]}..."):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**作者:** {authors_str}")
                        st.markdown(f"**来源:** {article.get('source', 'N/A')} | **年份:** {article.get('year', 'N/A')}")
                        st.markdown(f"**期刊:** {article.get('journal', 'N/A')}")
                    with col_b:
                        url = article.get('url', '')
                        if url:
                            st.markdown(f"[🔗 查看原文]({url})")
                        doi = article.get('doi', '')
                        if doi:
                            st.caption(f"DOI: {doi}")

                    abstract = article.get('abstract', '')
                    if abstract:
                        st.markdown("**摘要:**")
                        st.markdown(abstract[:1000])
                    else:
                        st.warning("暂无摘要")

        # 导出按钮
        if result['articles']:
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                review_text = f"# 文献综述：{result['query']}\n\n{result['structured_review']}\n\n---\n# 简明摘要\n\n{result['abstract_summary']}"
                st.download_button(
                    "📥 下载综述报告 (Markdown)",
                    review_text,
                    file_name=f"literature_review_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown",
                )
            with col_exp2:
                try:
                    bibtex_result = APIClient.literature_export_bibtex(result['articles'])
                    st.download_button(
                        "📥 下载 BibTeX 引用",
                        bibtex_result['bibtex'],
                        file_name=f"references_{datetime.now().strftime('%Y%m%d_%H%M')}.bib",
                        mime="text/plain",
                    )
                except APIError:
                    pass  # BibTeX export failure is non-critical

# ============================================================
# 模块2：研究空白与前沿探测
# ============================================================
elif function.startswith("🔍"):
    st.header("🔍 研究空白与前沿探测")
    st.markdown("*分析文献热点、追踪研究趋势、探测潜在研究空白*")

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input(
            "研究领域 / 主题",
            placeholder="例如：阿尔茨海默病早期诊断、量子计算纠错、气候变化对农业的影响...",
            key="gap_topic",
        )
    with col2:
        deep_mode = st.checkbox("深度分析模式", value=True, help="检索更多文献，进行更深入的分析")

    analyze_btn = st.button("🔍 开始分析", type="primary")

    if analyze_btn and topic:
        with st.spinner("🔄 正在分析研究热点和空白（可能需要30-60秒）..."):
            try:
                result = APIClient.gap_analyze(topic, deep_search=deep_mode)
                st.session_state.gap_analysis = result
                st.success("✅ 分析完成！")
                # 自动保存
                try:
                    APIClient.history_save("gap", topic[:50], topic, result)
                except Exception:
                    pass
            except APIError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ 未知错误: {str(e)}")

    if st.session_state.gap_analysis:
        result = st.session_state.gap_analysis

        # 关键词标签
        if result.get('hot_keywords') or result.get('emerging_keywords'):
            st.subheader("🏷️ 关键主题词")
            col_hot, col_emerg = st.columns(2)
            with col_hot:
                st.markdown("**🔥 热门关键词**")
                if result['hot_keywords']:
                    tags = " ".join([f"`{kw}`" for kw in result['hot_keywords'][:10]])
                    st.markdown(tags, unsafe_allow_html=True)
                else:
                    st.caption("暂无")
            with col_emerg:
                st.markdown("**🚀 新兴关键词**")
                if result['emerging_keywords']:
                    tags = " ".join([f"`{kw}`" for kw in result['emerging_keywords'][:10]])
                    st.markdown(tags, unsafe_allow_html=True)
                else:
                    st.caption("暂无")

        # 三个分析维度
        tab_hot, tab_trend, tab_gap = st.tabs([
            "🔥 研究热点分析",
            "📈 研究趋势与前沿",
            "💡 研究空白与未来方向",
        ])

        with tab_hot:
            if result['hotspots']:
                st.markdown(result['hotspots'])
            else:
                st.info("无热点分析数据")

        with tab_trend:
            if result['trends']:
                st.markdown(result['trends'])
            else:
                st.info("无趋势分析数据")

        with tab_gap:
            if result['gaps']:
                st.markdown(result['gaps'])
            else:
                st.info("无空白分析数据")

        # 导出
        if result['hotspots']:
            full_analysis = f"""# 研究空白与前沿分析：{result['topic']}

## 🔥 研究热点
{result['hotspots']}

## 📈 研究趋势
{result['trends']}

## 💡 研究空白
{result['gaps']}

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
            st.download_button(
                "📥 下载完整分析报告",
                full_analysis,
                file_name=f"gap_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )

# ============================================================
# 模块3：实验方案设计建议
# ============================================================
elif function.startswith("🧪"):
    st.header("🧪 实验方案设计建议")
    st.markdown("*针对科学问题自动生成实验设计、技术路线和方法推荐*")

    research_question = st.text_area(
        "研究问题 / 科学假设",
        placeholder="例如：研究 METTL3 介导的 m6A 修饰在非小细胞肺癌耐药中的作用机制...\n请尽量详细描述您的研究问题，包括背景、目标和预期。",
        height=120,
        key="exp_question",
    )

    col1, col2 = st.columns(2)
    with col1:
        gen_design_btn = st.button("🧪 生成实验设计方案", type="primary", use_container_width=True)
    with col2:
        rec_methods_btn = st.button("🔬 推荐实验方法", use_container_width=True)

    if research_question:
        if gen_design_btn:
            with st.spinner("🔄 正在设计实验方案（可能需要30-60秒）..."):
                try:
                    result = APIClient.experiment_design(research_question, search_methods=True)
                    st.session_state.experiment_design = result
                    st.success("✅ 方案生成完成！")
                    # 自动保存
                    try:
                        APIClient.history_save("experiment", research_question[:50], research_question, result)
                    except Exception:
                        pass
                except APIError as e:
                    st.error(f"❌ {str(e)}")
                except Exception as e:
                    st.error(f"❌ 未知错误: {str(e)}")

        if rec_methods_btn:
            with st.spinner("🔄 正在分析推荐方法..."):
                try:
                    methods_result = APIClient.experiment_recommend_methods(research_question)
                    if st.session_state.experiment_design:
                        st.session_state.experiment_design['method_recommendations'] = methods_result['recommendations']
                    else:
                        st.session_state.experiment_design = {
                            'research_question': research_question,
                            'full_design': '',
                            'method_recommendations': methods_result['recommendations'],
                        }
                    st.success("✅ 方法推荐完成！")
                except APIError as e:
                    st.error(f"❌ {str(e)}")
                except Exception as e:
                    st.error(f"❌ 未知错误: {str(e)}")

    # 显示结果
    if st.session_state.experiment_design:
        design = st.session_state.experiment_design

        tab_design, tab_methods, tab_validate = st.tabs([
            "📐 完整实验方案",
            "🔧 方法推荐",
            "✅ 设计验证",
        ])

        with tab_design:
            if design.get('full_design'):
                st.markdown(design['full_design'])
            elif not gen_design_btn:
                st.info("点击「生成实验设计方案」按钮开始")
            else:
                st.info("等待生成...")

        with tab_methods:
            if design.get('method_recommendations'):
                st.markdown(design['method_recommendations'])
            elif not rec_methods_btn:
                st.info("点击「推荐实验方法」按钮获取推荐")
            else:
                st.info("等待生成...")

        with tab_validate:
            if design.get('full_design'):
                try:
                    validation = APIClient.experiment_validate(design['full_design'])

                    st.subheader("设计完整性检查")
                    check_labels = {
                        'hypothesis': '研究假设',
                        'control_group': '对照组设计',
                        'sample_size': '样本量估算',
                        'variables': '变量控制',
                        'statistical_analysis': '统计分析方案',
                        'expected_results': '预期结果分析',
                        'limitations': '局限性讨论',
                    }
                    for check_name, passed in validation['checks'].items():
                        label = check_labels.get(check_name, check_name)
                        icon = "✅" if passed else "⚠️"
                        st.markdown(f"{icon} {label}")

                    st.metric("完整度评分", validation['completeness'])
                except APIError as e:
                    st.warning(f"验证失败: {str(e)}")
            else:
                st.info("请先生成实验设计方案")

        # 导出
        if design.get('full_design'):
            full_text = f"""# 实验设计方案

## 研究问题
{design['research_question']}

---

## 完整实验方案
{design['full_design']}

---

## 方法推荐
{design.get('method_recommendations', '（未生成）')}

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
            st.download_button(
                "📥 下载实验方案",
                full_text,
                file_name=f"experiment_design_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )

# ============================================================
# 模块4：论文写作辅助
# ============================================================
elif function.startswith("✍️"):
    st.header("✍️ 论文写作辅助")
    st.markdown("*根据实验数据和笔记，辅助生成论文各章节草稿*")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📝 写作素材")

        paper_title = st.text_input("论文标题", placeholder="输入论文标题...", key="paper_title")

        journal_style = st.selectbox(
            "目标期刊风格",
            JOURNAL_STYLES,
            index=len(JOURNAL_STYLES)-1 if JOURNAL_STYLES else 0,
        )

        background = st.text_area(
            "研究背景与文献回顾",
            placeholder="输入已有研究背景、相关文献要点...",
            height=120,
            key="bg",
        )

        methods_desc = st.text_area(
            "实验方法描述",
            placeholder="输入实验设计、方法、步骤、材料...",
            height=120,
            key="methods_desc",
        )

    with col_right:
        st.subheader("📊 数据与结果")

        results_data = st.text_area(
            "实验结果与数据",
            placeholder="输入实验结果、数据、图表说明...\n例如：实验组相比对照组显著提高 (p<0.01)...",
            height=120,
            key="results_data",
        )

        notes = st.text_area(
            "讨论要点与笔记",
            placeholder="输入讨论要点、重要发现、与文献的比较、局限性...",
            height=120,
            key="notes",
        )

        references = st.text_area(
            "参考文献",
            placeholder="输入参考文献列表，每行一条...",
            height=100,
            key="refs",
        )

    st.divider()

    # 章节生成按钮
    st.subheader("🎯 选择要生成的章节")
    col_sec1, col_sec2, col_sec3, col_sec4, col_sec5 = st.columns(5)

    section_to_generate = None

    with col_sec1:
        if st.button("📋 摘要\nAbstract", use_container_width=True):
            section_to_generate = 'abstract'
    with col_sec2:
        if st.button("📖 引言\nIntroduction", use_container_width=True):
            section_to_generate = 'introduction'
    with col_sec3:
        if st.button("🔬 方法\nMethods", use_container_width=True):
            section_to_generate = 'methods'
    with col_sec4:
        if st.button("📊 结果\nResults", use_container_width=True):
            section_to_generate = 'results'
    with col_sec5:
        if st.button("💬 讨论\nDiscussion", use_container_width=True):
            section_to_generate = 'discussion'

    col_full1, col_full2 = st.columns(2)
    with col_full1:
        if st.button("📝 生成完整论文（所有章节）", type="primary", use_container_width=True):
            section_to_generate = 'full'

    # 构建上下文
    context = {
        'title': paper_title,
        'background': background or '(未提供)',
        'experimental_data': results_data or '(未提供)',
        'methods_description': methods_desc or '(未提供)',
        'results_data': results_data or '(未提供)',
        'notes': notes or '(未提供)',
        'references': [r.strip() for r in references.split('\n') if r.strip()] if references else [],
    }

    # 执行生成
    if section_to_generate and paper_title:
        if section_to_generate == 'full':
            with st.spinner("🔄 正在生成完整论文草稿（这可能需要1-3分钟）..."):
                try:
                    draft = APIClient.paper_generate_full(context, journal_style)
                    st.session_state.paper_draft = draft
                    st.success("✅ 论文草稿生成完成！")
                    # 自动保存
                    try:
                        APIClient.history_save("paper", paper_title[:50], paper_title, draft)
                    except Exception:
                        pass
                except APIError as e:
                    st.error(f"❌ {str(e)}")
                except Exception as e:
                    st.error(f"❌ 未知错误: {str(e)}")
        else:
            section_names = {
                'abstract': '摘要', 'introduction': '引言',
                'methods': '方法', 'results': '结果', 'discussion': '讨论',
            }
            with st.spinner(f"🔄 正在生成{section_names.get(section_to_generate, section_to_generate)}章节..."):
                try:
                    section_result = APIClient.paper_generate_section(
                        section_to_generate, context, journal_style
                    )

                    if not st.session_state.paper_draft:
                        st.session_state.paper_draft = {
                            'title': paper_title,
                            'abstract': '',
                            'introduction': '',
                            'methods': '',
                            'results': '',
                            'discussion': '',
                            'references': context.get('references', []),
                            'target_journal_style': journal_style,
                        }

                    st.session_state.paper_draft[section_to_generate] = section_result['content']
                    st.success(f"✅ {section_names.get(section_to_generate)}章节生成完成！")
                except APIError as e:
                    st.error(f"❌ {str(e)}")
                except Exception as e:
                    st.error(f"❌ 未知错误: {str(e)}")

    # 显示生成的草稿
    if st.session_state.paper_draft:
        draft = st.session_state.paper_draft

        st.divider()
        st.subheader(f"📄 论文草稿：{draft.get('title', 'Untitled')}")

        st.caption(f"目标风格：{draft.get('target_journal_style', '通用学术规范')}")

        sections = [
            ('abstract', '📋 摘要'),
            ('introduction', '📖 引言'),
            ('methods', '🔬 方法'),
            ('results', '📊 结果'),
            ('discussion', '💬 讨论'),
        ]

        for section_key, section_label in sections:
            section_content = draft.get(section_key, '')
            if section_content:
                with st.expander(section_label, expanded=(section_key == 'abstract')):
                    st.markdown(section_content)

        # 写作提示
        with st.expander("💡 写作提示", expanded=False):
            selected_section = st.selectbox(
                "选择章节查看写作提示",
                ['abstract', 'introduction', 'methods', 'results', 'discussion'],
                format_func=lambda x: {
                    'abstract': '摘要', 'introduction': '引言',
                    'methods': '方法', 'results': '结果', 'discussion': '讨论',
                }.get(x, x),
            )
            try:
                tips_result = APIClient.paper_writing_tips(selected_section, journal_style)
                st.info(tips_result.get('tips', '暂无写作提示'))
            except APIError:
                st.info("无法获取写作提示（后端连接失败）")

        # 导出
        full_paper = f"""# {draft.get('title', 'Untitled')}

---

## 摘要
{draft.get('abstract', '(未生成)')}

---

## 引言
{draft.get('introduction', '(未生成)')}

---

## 方法
{draft.get('methods', '(未生成)')}

---

## 结果
{draft.get('results', '(未生成)')}

---

## 讨论
{draft.get('discussion', '(未生成)')}

---

**目标期刊风格:** {draft.get('target_journal_style', '通用学术规范')}
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        st.download_button(
            "📥 下载完整论文草稿",
            full_paper,
            file_name=f"paper_draft_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
        )

# ============================================================
# 页脚
# ============================================================
if function == "🧠 5. PDF 文献问答":
    from library_page import render
    render()

if function == "🔗 研究工作台":
    from workspace_page import render
    render()

st.divider()
st.caption(f"🔬 {APP_NAME} v{APP_VERSION} | 前后端分离架构 | Powered by DeepSeek LLM | PubMed + arXiv")

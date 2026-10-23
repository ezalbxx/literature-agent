"""Evidence-first interface; offline by default, paid calls explicitly selected."""
import json
import requests
import streamlit as st
from api_client import BACKEND_URL, APIClient, APIError


def render():
    st.header('🧠 PDF 文献问答')
    st.caption('导入论文 → 检索原文 → 工具调用问答 → 核对页码与引文')
    st.info('默认离线演示：不请求任何大模型。扫描 PDF 需先 OCR；当前检索为 BM25 关键词检索。')
    try:
        collection = st.session_state.get('library_collection')
        entered = st.text_input('文献库 ID（留空可新建；复制 ID 可在重启后继续使用）', value=collection or '')
        left, right = st.columns(2)
        if left.button('新建文献库'):
            result = APIClient._post('/api/library/collections', {})
            st.session_state.library_collection = result['collection']
            st.rerun()
        if entered and right.button('打开此文献库'):
            APIClient._get(f'/api/library/{entered}/documents')
            st.session_state.library_collection = entered
            st.rerun()
        if not collection:
            st.write('先新建一个文献库，或输入已有 ID。')
            return
        st.code(collection, language=None)
        files = st.file_uploader('导入带文本层的 PDF（单份 ≤20 MiB、≤100 页）', type=['pdf'], accept_multiple_files=True)
        if st.button('导入所选 PDF', disabled=not files):
            for file in files:
                response = requests.post(f'{BACKEND_URL}/api/library/{collection}/pdf',
                                         files={'file': (file.name, file.getvalue(), 'application/pdf')}, timeout=60)
                if response.ok:
                    item = response.json()
                    st.success(f"{file.name}：{'已存在' if item['duplicate'] else '已导入'}，{item['chunks']} 个片段")
                else:
                    st.error(response.json().get('detail', '导入失败'))
        if st.session_state.get('current_articles') and st.button('导入跨库检索的摘要'):
            records = [{'title': a['title'][:300], 'abstract': a.get('abstract', '')[:30000], 'url': a.get('url', '')}
                       for a in st.session_state.current_articles if len(a.get('abstract', '')) >= 12]
            if records:
                APIClient._post(f'/api/library/{collection}/articles', {'articles': records[:100]})
                st.success('已导入摘要；摘要证据不代表阅读全文。')
        if st.button('载入免密钥示例资料'):
            APIClient._post(f'/api/library/{collection}/articles', {'articles': [{
                'title': 'Synthetic RAG demonstration note',
                'abstract': 'Retrieval augmented generation retrieves relevant document passages before producing an answer. '
                            'Each citation records the original document, page and verbatim evidence quote. '
                            'This is a synthetic demonstration note, not a published research paper.', 'url': ''}]})
            st.success('示例已导入（合成资料，不是真实论文）。')
        docs = APIClient._get(f'/api/library/{collection}/documents')['documents']
        with st.expander(f'文献库：{len(docs)} 份资料'):
            st.dataframe(docs, use_container_width=True)
        question = st.text_input('问题', placeholder='例如：retrieval augmented generation 如何引用原文？')
        live = st.checkbox('使用已配置模型问答（会向模型服务发送问题和检索片段，并消耗 API 额度）', value=False)
        a, b = st.columns(2)
        if a.button('只检索证据', disabled=not question.strip()):
            result = APIClient._post(f'/api/library/{collection}/search', {'query': question})
            st.session_state.library_evidence = result['chunks']
        if b.button('模型问答' if live else '运行离线演示', disabled=not question.strip()):
            with st.spinner('正在运行工具调用流程…'):
                st.session_state.library_answer = APIClient._post(f'/api/library/{collection}/ask', {
                    'question': question, 'offline_demo': not live})
                st.session_state.library_answer_question = question
        for chunk in st.session_state.get('library_evidence', []):
            with st.expander(f"{chunk['title']} · {'摘要' if chunk['kind']=='abstract' else '第 '+str(chunk['page'])+' 页'} · {chunk['id']}"):
                st.write(chunk['text'])
        result = st.session_state.get('library_answer')
        if result:
            st.subheader(st.session_state.get('library_answer_question', '问答结果'))
            if result['mode'] == 'offline_demo':
                st.warning('这是确定性的流程演示，内容未经过真实模型推理。')
            if result['status'] != 'answered':
                st.warning('证据不足或达到调用预算，未输出可接受答案。')
            for i, claim in enumerate(result['claims'], 1):
                st.write(f"{i}. {claim['text']}")
                for cite in claim['citations']:
                    label = '摘要' if cite['kind']=='abstract' else f"第 {cite['page']} 页"
                    with st.expander(f"依据：{cite['title']} · {label}"):
                        st.write(cite['quote'])
                        st.code(cite['id'], language=None)
                        if cite['url'].startswith(('http://', 'https://')):
                            st.link_button('打开原文来源', cite['url'])
            st.caption('检查通过表示引用编号和原文片段匹配；是否充分支持结论仍需人工核对。')
            with st.expander('查看工具调用记录'):
                st.json(result['trace'])
            st.download_button('导出问答与证据记录', json.dumps(result, ensure_ascii=False, indent=2),
                               file_name='literature-answer.json', mime='application/json')
    except APIError as exc:
        st.error(str(exc))
    except requests.RequestException:
        st.error('后端连接失败，请检查服务。')

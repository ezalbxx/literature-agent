"""Research handoff dashboard; shows artifacts and actual message envelopes."""
import json
import streamlit as st
from api_client import APIClient, APIError


LABELS = {'review':'① 文献综述', 'gaps':'② 空白与问题', 'experiment':'③ 实验方案', 'draft':'④ 写作提案'}


def render():
    st.header('🔗 研究工作台')
    st.write('五个功能共享同一个文献库，并通过结构化产物交接。先准备资料，再逐步推进。')
    st.caption('当前是程序编排的多角色流水线；PDF 问答支持模型自主工具调用。角色间共享产物，不创建后台模型会话。')
    try:
        topic = st.text_input('研究主题（用原文中出现的术语，便于检索）', key='workspace_topic')
        reuse = st.checkbox('使用当前 PDF 文献库', value=bool(st.session_state.get('library_collection')))
        if st.button('新建研究工作区', disabled=not topic.strip()):
            payload = {'topic':topic}
            if reuse and st.session_state.get('library_collection'):
                payload['collection'] = st.session_state.library_collection
            result = APIClient._post('/api/workspaces', payload)
            st.session_state.research_workspace = result['id']
            st.session_state.library_collection = result['collection']
            st.rerun()
        existing = st.text_input('打开已有工作区 ID')
        if st.button('打开工作区', disabled=not existing.strip()):
            result = APIClient._get(f'/api/workspaces/{existing.strip()}')
            st.session_state.research_workspace = result['id']
            st.session_state.library_collection = result['collection']
            st.rerun()
        identifier = st.session_state.get('research_workspace')
        if not identifier:
            st.info('新建工作区后，在「5. PDF 文献问答」导入资料；也可导入「1. 跨库检索」已有摘要。')
            return
        state = APIClient._get(f'/api/workspaces/{identifier}')
        st.session_state.library_collection = state['collection']
        st.subheader(state['topic'])
        st.code(f"工作区 ID：{identifier}\n文献库 ID：{state['collection']}", language=None)
        st.info('资料入口：「1. 跨库检索」取回摘要；「5. PDF 文献问答」导入摘要或 PDF。新增资料会使本工作区旧分析失效。')
        if st.button('载入联动演示资料'):
            APIClient._post(f"/api/library/{state['collection']}/articles", {'articles':[{
                'title':'Synthetic research coordination note',
                'abstract':f"{state['topic']}. Retrieval augmented generation retrieves passages before answering. "
                           'Citation evidence includes a document identifier and verbatim quotation. '
                           'This is synthetic demonstration material, not a published paper.', 'url':''}]})
            st.rerun()
        live = st.checkbox('使用真实模型运行研究角色（发送共享上下文到已配置服务，产生 API 费用）', value=False)
        if not live:
            st.warning('离线联动演示：综述、问题、方案和草稿均为固定样例，不是实际研究成果。')
        st.write('状态：'+' → '.join(f"{'✓' if key in state['artifacts'] else '○'} {label}" for key,label in LABELS.items()))
        for stage, label in LABELS.items():
            with st.expander(label, expanded=stage not in state['artifacts']):
                if st.button(f'运行{label}', key=f'run_{stage}'):
                    with st.spinner('读取共享证据和上游产物，生成本阶段结果…'):
                        APIClient._post(f'/api/workspaces/{identifier}/run', {'stage':stage,'offline_demo':not live})
                    st.rerun()
                artifact = state['artifacts'].get(stage)
                if artifact:
                    st.caption(f"{artifact['role']} · {artifact['mode']} · 需人工审阅 · 产物 {artifact['id']}")
                    for key, value in artifact['content'].items():
                        if key == 'evidence':
                            with st.expander('本阶段引用依据'):
                                st.json(value)
                        else:
                            st.markdown(f'**{key}**')
                            if isinstance(value, list):
                                for item in value:
                                    st.write(item)
                            else:
                                st.write(value)
                    if stage == 'gaps':
                        candidates = artifact['content']['candidates']
                        selected = st.selectbox('确认要继续的研究问题', range(len(candidates)),
                            format_func=lambda i:candidates[i]['question'],
                            index=state.get('selected_candidate') or 0)
                        if st.button('将选定问题交给实验设计角色'):
                            APIClient._post(f'/api/workspaces/{identifier}/select', {'candidate_index':selected})
                            st.rerun()
        if state['selected_question']:
            st.success('已确认问题：'+state['selected_question'])
        st.caption('实验方案与写作提案中的实验均未开展；生成流程不会声称已经得到实验结果。')
        with st.expander(f"角色消息与产物交接（{len(state['messages'])} 条）"):
            st.json(state['messages'])
        st.download_button('导出完整研究工作区', json.dumps(state,ensure_ascii=False,indent=2),
                           file_name='research-workspace.json',mime='application/json')
    except APIError as exc:
        st.error(str(exc))

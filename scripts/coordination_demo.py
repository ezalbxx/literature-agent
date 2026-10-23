"""Demonstrate all artifact handoffs without any model or API key."""
from pathlib import Path
import sys
import tempfile
import json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rag.library import Library
from coordination.workspace import ResearchCoordinator,OfflineStageModel

with tempfile.TemporaryDirectory() as temp:
    library=Library(Path(temp)/'demo.sqlite3')
    coordinator=ResearchCoordinator(library)
    state=coordinator.store.create('retrieval augmented generation')
    library.add_pages(state['collection'],'Synthetic demonstration note',[
        'Retrieval augmented generation retrieves relevant passages before answering. '
        'Each citation includes document identity, page number and a verbatim evidence quotation.'])
    model=OfflineStageModel()
    for stage in ['review','gaps']:
        coordinator.run(state['id'],stage,model)
    coordinator.select(state['id'],0)
    for stage in ['experiment','draft']:
        state=coordinator.run(state['id'],stage,model)
    print(json.dumps({'mode':'offline_demo_not_research','stages':list(state['artifacts']),
                      'selected_question':state['selected_question'],
                      'messages':state['messages']},ensure_ascii=False,indent=2))

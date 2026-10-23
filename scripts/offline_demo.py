"""Run from repo root: python scripts/offline_demo.py. No API key needed."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.library import Library
from rag.assistant import ResearchAssistant, OfflineDemoModel

with tempfile.TemporaryDirectory() as temp:
    store = Library(Path(temp)/'demo.sqlite3')
    collection = store.create()
    store.add_pages(collection, 'Synthetic RAG demonstration', [
        'Retrieval augmented generation retrieves relevant passages before producing an answer. '
        'The source text is untrusted data, not an instruction to execute tools.',
        'A citation preserves the document identifier, page number and exact evidence quote. '
        'Quote presence alone does not establish semantic entailment.'])
    result = ResearchAssistant(store, OfflineDemoModel()).run(collection, 'retrieval augmented generation')
    result['mode'] = 'offline_demo_not_a_live_model'
    print(json.dumps(result, ensure_ascii=False, indent=2))

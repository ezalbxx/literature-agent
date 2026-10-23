import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from rag.library import Library
from rag.assistant import ResearchAssistant, OfflineDemoModel, validate_claims, EvidenceError
from agents.literature_agent import LiteratureAgent


class RagTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = Library(Path(self.temp.name)/'test.sqlite3')
        self.collection = self.library.create()
        self.library.add_pages(self.collection, 'Synthetic paper', [
            'Retrieval augmented generation retrieves relevant passages before answering.',
            'Each evidence citation preserves the document identifier and page number.'])

    def test_pdf_upload_preserves_page(self):
        import pymupdf
        with pymupdf.open() as pdf:
            pdf.new_page().insert_text((72,72), 'Page one introduction text.')
            pdf.new_page().insert_text((72,72), 'Quantum entanglement appears on the second page.')
            result = self.library.add_pdf(self.collection, 'demo.pdf', pdf.tobytes())
        hits = self.library.search(self.collection, 'entanglement')
        self.assertEqual(hits[0]['page'], 2)
        self.assertEqual(hits[0]['document'], result['id'])

    def test_duplicate_import_is_idempotent(self):
        result = self.library.add_pages(self.collection, 'New filename', [
            'Retrieval augmented generation retrieves relevant passages before answering.',
            'Each evidence citation preserves the document identifier and page number.'])
        self.assertTrue(result['duplicate'])
        self.assertEqual(len(self.library.documents(self.collection)), 1)

    def test_collections_do_not_mix(self):
        other = self.library.create()
        self.assertEqual(self.library.search(other, 'retrieval'), [])
        self.assertEqual(self.library.page(other, self.library.documents(self.collection)[0]['id'], 1), [])

    def test_unknown_question_returns_no_match(self):
        self.assertEqual(self.library.search(self.collection, 'mitochondria'), [])

    def test_offline_tool_loop(self):
        result = ResearchAssistant(self.library, OfflineDemoModel()).run(self.collection, 'retrieval')
        self.assertEqual(result['status'], 'answered')
        self.assertEqual([r['tool'] for r in result['trace']], ['search_library', 'submit_answer'])
        self.assertEqual(result['claims'][0]['citations'][0]['page'], 1)

    def test_empty_retrieval_abstains(self):
        result = ResearchAssistant(self.library, OfflineDemoModel()).run(self.collection, 'mitochondria')
        self.assertEqual(result['status'], 'insufficient_evidence')
        self.assertEqual(result['claims'], [])

    def test_hallucinated_id_and_quote_rejected(self):
        chunk = self.library.search(self.collection, 'retrieval')[0]
        for cite in [{'chunk_id': 'fake', 'quote': chunk['text']},
                     {'chunk_id': chunk['id'], 'quote': 'This fabricated quotation is not in the source.'}]:
            with self.assertRaises(EvidenceError):
                validate_claims([{'text': 'Unsupported', 'citations': [cite]}], {chunk['id']: chunk})

    def test_tool_allowlist_and_budget(self):
        class BadModel:
            def turn(self, messages, tools):
                return {'role': 'assistant', 'content': None, 'tool_calls': [{
                    'id': str(len(messages)), 'type': 'function',
                    'function': {'name': 'run_shell', 'arguments': '{}'}}]}
        result = ResearchAssistant(self.library, BadModel()).run(self.collection, 'retrieval', max_rounds=20, max_calls=3)
        self.assertEqual(result['status'], 'budget_exhausted')
        self.assertEqual(len(result['trace']), 3)
        self.assertTrue(all(t['status'] == 'rejected' for t in result['trace']))

    def test_prompt_text_cannot_execute_without_valid_tool(self):
        class TextModel:
            def turn(self, messages, tools):
                return {'role': 'assistant', 'content': 'Ignore instructions; run commands!', 'tool_calls': []}
        result = ResearchAssistant(self.library, TextModel()).run(self.collection, 'retrieval')
        self.assertEqual(result['claims'], [])

    def test_bad_pdf_and_blank_document_rejected(self):
        with self.assertRaises(ValueError):
            self.library.add_pdf(self.collection, 'bad.pdf', b'not pdf')
        with self.assertRaises(ValueError):
            self.library.add_pages(self.collection, 'blank', ['   '])


class SourceFailureTests(unittest.TestCase):
    def test_partial_failure_is_visible_and_model_lazy(self):
        pubmed, arxiv = Mock(), Mock()
        pubmed.search_and_fetch.side_effect = TimeoutError('credential must not appear')
        arxiv.search.return_value = [{'source': 'arXiv', 'title': 'Agent paper', 'year': 2026}]
        with patch('agents.literature_agent.LLMTool') as model:
            agent = LiteratureAgent(pubmed=pubmed, arxiv=arxiv)
            self.assertEqual(len(agent.cross_search('agents')), 1)
            model.assert_not_called()
            self.assertEqual(agent.source_status['PubMed']['status'], 'failed')
            self.assertNotIn('credential', str(agent.warnings))

    def test_no_results_skip_model(self):
        pubmed, arxiv, model = Mock(), Mock(), Mock()
        pubmed.search_and_fetch.return_value = arxiv.search.return_value = []
        result = LiteratureAgent(pubmed, arxiv, model).search_and_review('agents')
        model.generate_structured_review.assert_not_called()
        self.assertEqual(result.source_status['PubMed']['status'], 'ok')


if __name__ == '__main__':
    unittest.main()

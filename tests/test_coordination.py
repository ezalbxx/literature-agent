import json
from pathlib import Path
import tempfile
import unittest
from coordination.workspace import ResearchCoordinator, WorkspaceStore, OfflineStageModel
from rag.library import Library


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = Library(Path(self.temp.name)/'library.sqlite3')
        self.coordinator = ResearchCoordinator(self.library)
        self.state = self.coordinator.store.create('retrieval')
        self.identifier = self.state['id']
        self.collection = self.state['collection']
        self.library.add_pages(self.collection,'Synthetic evidence',[
            'Retrieval augmented generation retrieves evidence before answering. '
            'Evidence references preserve page numbers and document identifiers.'])

    def test_complete_pipeline_passes_artifact_ids(self):
        model = OfflineStageModel()
        review = self.coordinator.run(self.identifier,'review',model)['artifacts']['review']
        gaps = self.coordinator.run(self.identifier,'gaps',model)['artifacts']['gaps']
        self.assertEqual(gaps['upstream_artifacts'], [review['id']])
        self.coordinator.select(self.identifier,0)
        experiment = self.coordinator.run(self.identifier,'experiment',model)['artifacts']['experiment']
        final = self.coordinator.run(self.identifier,'draft',model)
        self.assertIn(experiment['id'], final['artifacts']['draft']['upstream_artifacts'])
        self.assertEqual(final['artifacts']['draft']['results_status'],'not_conducted')
        self.assertTrue(any(m['sender']=='GapAgent' and m['recipient']=='ExperimentAgent' for m in final['messages']))

    def test_cannot_skip_human_question_selection(self):
        model = OfflineStageModel()
        self.coordinator.run(self.identifier,'review',model)
        self.coordinator.run(self.identifier,'gaps',model)
        with self.assertRaises(ValueError):
            self.coordinator.run(self.identifier,'experiment',model)

    def test_new_document_invalidates_downstream(self):
        self.coordinator.run(self.identifier,'review',OfflineStageModel())
        self.library.add_pages(self.collection,'New evidence',['New retrieval evidence changes the original document corpus.'])
        self.assertEqual(self.coordinator.sync(self.identifier)['artifacts'], {})

    def test_rerunning_review_invalidates_gaps(self):
        model = OfflineStageModel()
        self.coordinator.run(self.identifier,'review',model)
        self.coordinator.run(self.identifier,'gaps',model)
        state = self.coordinator.run(self.identifier,'review',model)
        self.assertNotIn('gaps', state['artifacts'])

    def test_demo_cannot_feed_live_research(self):
        self.coordinator.run(self.identifier,'review',OfflineStageModel())
        with self.assertRaises(ValueError):
            self.coordinator.run(self.identifier,'gaps',OfflineStageModel(),offline_demo=False)

    def test_invalid_citations_never_persist(self):
        class BadModel(OfflineStageModel):
            def turn(self, messages, tools):
                response = super().turn(messages,tools)
                args = json.loads(response['tool_calls'][0]['function']['arguments'])
                args['evidence'][0]['citations'][0]['chunk_id'] = 'not-retrieved'
                response['tool_calls'][0]['function']['arguments'] = json.dumps(args)
                return response
        with self.assertRaises(ValueError):
            self.coordinator.run(self.identifier,'review',BadModel())
        self.assertEqual(self.coordinator.store.get(self.identifier)['artifacts'], {})

    def test_stale_writer_cannot_overwrite_state(self):
        state = self.coordinator.sync(self.identifier)
        self.coordinator.store.save(state,state['version'])
        with self.assertRaises(ValueError):
            self.coordinator.store.save(state,state['version'])


if __name__ == '__main__':
    unittest.main()

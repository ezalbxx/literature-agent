import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app


class ApiTests(unittest.TestCase):
    def test_complete_offline_library_workflow(self):
        with tempfile.TemporaryDirectory() as temp, patch('backend.routers.library.DATA_DIR', temp):
            client = TestClient(app)
            collection = client.post('/api/library/collections').json()['collection']
            prefix = f'/api/library/{collection}'
            result = client.post(prefix+'/articles', json={'articles': [{
                'title': 'Synthetic evidence', 'abstract': 'Retrieval augmented generation retrieves passages before answering.'}]})
            self.assertEqual(result.status_code, 200)
            result = client.post(prefix+'/ask', json={'question': 'retrieval'})
            self.assertEqual(result.json()['status'], 'answered')
            self.assertEqual(result.json()['mode'], 'offline_demo')
            self.assertEqual(client.post(prefix+'/search', json={'query': 'retrieval', 'limit': 999}).status_code, 422)
            self.assertEqual(client.post(prefix+'/pdf', files={'file': ('bad.pdf', b'not a pdf')}).status_code, 422)
            self.assertEqual(client.get('/api/library/not-a-collection/documents').status_code, 404)

    def test_live_model_failure_is_http_error_not_answer(self):
        with tempfile.TemporaryDirectory() as temp, patch('backend.routers.library.DATA_DIR', temp):
            client = TestClient(app)
            collection = client.post('/api/library/collections').json()['collection']
            with patch('backend.routers.library.OpenAIToolModel', side_effect=RuntimeError('Model unavailable')):
                result = client.post(f'/api/library/{collection}/ask', json={'question': 'agent', 'offline_demo': False})
            self.assertEqual(result.status_code, 502)


if __name__ == '__main__':
    unittest.main()

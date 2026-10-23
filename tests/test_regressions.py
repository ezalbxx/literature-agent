import unittest
from unittest.mock import Mock, patch

from agents.literature_agent import LiteratureAgent


def paper(title, doi='', year='2026', source='PubMed'):
    return dict(title=title, doi=doi, year=year, source=source,
                abstract='A test abstract.', authors=['Test Author'])


class RetrievalRegressions(unittest.TestCase):
    def agent(self, first, second):
        agent = LiteratureAgent.__new__(LiteratureAgent)
        agent.pubmed = Mock()
        agent.arxiv = Mock()
        agent.pubmed.search_and_fetch.return_value = first
        agent.arxiv.search.return_value = second
        return agent

    def test_shared_title_prefix_is_not_duplicate(self):
        prefix = 'An unusually long title about the design of reliable agents '
        agent = self.agent([paper(prefix + 'in games')], [paper(prefix + 'in medicine')])
        self.assertEqual(len(agent.cross_search('agents')), 2)

    def test_doi_aliases_are_deduplicated(self):
        agent = self.agent([paper('First version', 'https://doi.org/10.1000/TEST')],
                           [paper('A different preprint title', '10.1000/test')])
        self.assertEqual(len(agent.cross_search('agents')), 1)

    def test_blank_query_never_calls_upstreams(self):
        agent = self.agent([], [])
        with self.assertRaises(ValueError):
            agent.cross_search('   ')
        agent.pubmed.search_and_fetch.assert_not_called()
        agent.arxiv.search.assert_not_called()


if __name__ == '__main__':
    unittest.main()

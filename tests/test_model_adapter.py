import unittest
from unittest.mock import Mock, patch
from rag.assistant import OpenAIToolModel


class AdapterTests(unittest.TestCase):
    def test_deepseek_disables_thinking_for_required_tools(self):
        fake = Mock()
        fake.provider, fake.model = 'deepseek', 'configured-model'
        message = Mock()
        message.content, message.tool_calls = None, []
        fake.client.with_options.return_value.chat.completions.create.return_value.choices = [Mock(message=message)]
        with patch('tools.llm_tool.LLMTool', return_value=fake):
            OpenAIToolModel().turn([{'role':'user','content':'hello'}], [])
        call = fake.client.with_options.return_value.chat.completions.create.call_args
        self.assertEqual(call.kwargs['extra_body'], {'thinking':{'type':'disabled'}})


if __name__ == '__main__':
    unittest.main()

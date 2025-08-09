import unittest
from unittest.mock import patch
from lmflux.core.components import LLMOptions, Message, SystemPrompt, TemplatedPrompt, ToolParam, Tool, Conversation

class TestLLMOptions(unittest.TestCase):
    def test_dict(self):
        options = LLMOptions(temperature=0.5)
        self.assertEqual(options.dict(), {'temperature': '0.5'})

class TestMessage(unittest.TestCase):
    def test_dump_message(self):
        message = Message("role", "content")
        self.assertEqual(message.dump_message(), {"role": "role", "content": "content"})

class TestSystemPrompt(unittest.TestCase):
    def test_get_message(self):
        prompt = SystemPrompt()
        message = prompt.get_message()
        self.assertIsInstance(message, Message)
class TestTemplatedPrompt(unittest.TestCase):
    @patch('lmflux.core.components.get_template')
    def test_get_message(self, mock_result):
        mock_result.return_value = 'mocked stuff'
        prompt = TemplatedPrompt("test_prompt", "role")
        message = prompt.get_message({})
        self.assertIsInstance(message, Message)

class TestToolParam(unittest.TestCase):
    def test_make_definition(self):
        param = ToolParam("type", "name")
        name, data, _ = param.make_definition()
        self.assertEqual(name, "name")

class TestTool(unittest.TestCase):
    def test_build_tool_calls(self):
        root_param = ToolParam(
            type="object",
            name="parameters",
            property=[ToolParam("object", "root")]
        )
        tool = Tool("name", "description", root_param, lambda: None)
        data = tool.build_tool_call()
        self.assertIsNotNone(data)

class TestConversation(unittest.TestCase):
    def test_dump_conversation(self):
        conversation = Conversation([Message("role", "content")])
        self.assertEqual(conversation.dump_conversation(), [{"role": "role", "content": "content"}])
        conversation_str = str(conversation)
    
    def test_conversation_can_act_as_list(self):
        conversation = Conversation([Message("role", "content")])
        len(conversation)
        _ = conversation[0]
        for message in conversation:
            str(message)
            message.dump_message()


if __name__ == '__main__':
    unittest.main()
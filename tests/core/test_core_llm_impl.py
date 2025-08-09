import unittest
from unittest.mock import Mock, patch, MagicMock
from lmflux.core.llm_impl import OpenAICompatibleEndpoint, NamedOAICompatible
from lmflux.core.components import SystemPrompt
from lmflux.core.llms import LLMModel
from lmflux.core.components import ToolParam, Tool

class TestOpenAICompatibleEndpoint(unittest.TestCase):
    @patch('openai.OpenAI')
    def test_init(self, mock_openai):
        mock_openai.return_value = MagicMock()
        model = OpenAICompatibleEndpoint("model_id", SystemPrompt())
        self.assertIsNotNone(model.client)
    
    @patch('openai.OpenAI')
    def test_compile_tools(self, mock_openai):
        mock_openai.return_value = MagicMock()
        model = OpenAICompatibleEndpoint("model_id", SystemPrompt())
        # Mock tools
        root_param = ToolParam(
            type="object",
            name="parameters",
            property=[ToolParam("object", "root")]
        )
        tool = Tool("name", "description", root_param, lambda: None)
        model.tools = [tool]
        model.__compile_tools__()
        self.assertIsNotNone(model.compiled_tools)

class TestNamedOAICompatible(unittest.TestCase):
    @patch('openai.OpenAI')
    def test_init(self, mock_openai):
        mock_openai.return_value = MagicMock()
        model = NamedOAICompatible("model_id", SystemPrompt())
        self.assertIsInstance(model, OpenAICompatibleEndpoint)

if __name__ == '__main__':
    unittest.main()
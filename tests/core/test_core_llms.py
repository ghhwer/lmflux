import unittest
from unittest.mock import Mock
from lmflux.core.llms import LLMModel
from lmflux.core.components import SystemPrompt, Message, LLMOptions, Tool, ToolParam

class EchoLLM(LLMModel):
    def __init__(self, model_id:str, system_prompt:SystemPrompt, options:LLMOptions=None):
        super().__init__(model_id=model_id, system_prompt=system_prompt, options=options)
    
    def __chat_endpoint__(self, tool_use_callback:callable) -> Message:
        return self.conversation[-1]

class TestLLMModel(unittest.TestCase):
    def test_init(self):
        model = EchoLLM("model_id", SystemPrompt())
        root_param = ToolParam(
            type="object",
            name="parameters",
            property=[ToolParam("object", "root")]
        )
        tool = Tool("name", "description", root_param, lambda: None)        
        model.add_tools(
            [tool]
        )
        self.assertEqual(model.model_id, "model_id")

    def test_chat(self):
        model = EchoLLM("model_id", SystemPrompt())
        # Mock chat_endpoint method
        with unittest.mock.patch.object(model, '__chat_endpoint__', return_value=[object()]):
            model.chat(object())

    def test_chat_with_callback(self):
        model = EchoLLM("model_id", SystemPrompt())
        def llm_callback(*arg, **kwargs):
            pass
        model.set_conversation_update_callback(llm_callback)
        # Mock chat_endpoint method
        with unittest.mock.patch.object(model, '__chat_endpoint__', return_value=[object()]):
            model.chat(object())


if __name__ == '__main__':
    unittest.main()
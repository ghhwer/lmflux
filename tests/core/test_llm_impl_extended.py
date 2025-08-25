import unittest
from unittest.mock import MagicMock, patch
import json

from lmflux.core.llm_impl import OpenAICompatibleEndpoint, NamedOAICompatible
from lmflux.core.components import SystemPrompt, ToolParam, Tool, Message, ToolRequest

class DummyCallback:
    def __init__(self):
        self.calls = []

    def __call__(self, tool_call, result):
        self.calls.append((tool_call, result))

def make_mock_message(role, content="", tool_calls=None, reasoning_content=None, call_id=None, name=None):
    """Helper to create a mock OpenAI message object."""
    mock_msg = MagicMock()
    mock_msg.role = role
    mock_msg.content = content
    mock_msg.reasoning_content = reasoning_content
    mock_msg.tool_calls = tool_calls
    mock_msg.tool_call_id = call_id
    mock_msg.name = name
    return mock_msg

def make_tool_call(id_, name, arguments):
    """Helper to create a mock tool call object mimicking OpenAI's structure."""
    func = MagicMock()
    func.name = name
    func.arguments = arguments
    tool_call = MagicMock()
    tool_call.id = id_
    tool_call.function = func
    return tool_call

class TestOpenAICompatibleEndpointChat(unittest.TestCase):
    @patch('openai.OpenAI')
    def test_chat_endpoint_without_tool_calls(self, mock_openai):
        # Setup mock client to return a single assistant message without tool calls
        mock_client = MagicMock()
        mock_message = make_mock_message(
            role="assistant",
            content="Hello, this is a response",
            tool_calls=None
        )
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
        mock_openai.return_value = mock_client

        endpoint = OpenAICompatibleEndpoint("model-id", SystemPrompt())
        result = endpoint.__chat_endpoint__(tool_use_callback=lambda *a: None)

        # Expect a single Message from the assistant
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].role, "assistant")
        self.assertEqual(result[0].content, "Hello, this is a response")

    @patch('openai.OpenAI')
    def test_chat_endpoint_with_tool_calls(self, mock_openai):
        # Prepare a dummy tool
        root_param = ToolParam(
            type="object",
            name="params",
            property=[]
        )
        dummy_tool = Tool(
            name="dummy_tool",
            description="A dummy tool for testing",
            root_param=root_param,
            func=lambda **kwargs: "dummy_result"
        )

        # First call returns a message that includes a tool call
        tool_call_obj = make_tool_call(
            id_="call-1",
            name="dummy_tool",
            arguments=json.dumps({})
        )
        first_message = make_mock_message(
            role="assistant",
            content="Please use the tool",
            tool_calls=[tool_call_obj]
        )
        first_choice = MagicMock()
        first_choice.message = first_message

        # Second call returns a normal assistant reply without tool calls
        second_message = make_mock_message(
            role="assistant",
            content="Final answer after tool execution",
            tool_calls=None
        )
        second_choice = MagicMock()
        second_choice.message = second_message

        mock_client = MagicMock()
        # side_effect to simulate two successive calls
        mock_client.chat.completions.create.side_effect = [
            MagicMock(choices=[first_choice]),
            MagicMock(choices=[second_choice])
        ]
        mock_openai.return_value = mock_client

        endpoint = OpenAICompatibleEndpoint("model-id", SystemPrompt())
        endpoint.tools = [dummy_tool]   # inject the dummy tool

        callback = DummyCallback()
        result = endpoint.__chat_endpoint__(tool_use_callback=callback)

        # Expect three messages: assistant with tool_call, tool response, final assistant
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].role, "assistant")
        self.assertEqual(result[0].content, "Please use the tool")
        self.assertEqual(result[1].role, "tool")
        self.assertEqual(result[1].content, "dummy_result")
        self.assertEqual(result[2].role, "assistant")
        self.assertEqual(result[2].content, "Final answer after tool execution")

        # Verify callback was invoked once with the correct tool call and result
        self.assertEqual(len(callback.calls), 1)
        called_tool, called_result = callback.calls[0]
        self.assertEqual(called_tool.raw_tool_call.id, "call-1")
        self.assertEqual(called_result, "dummy_result")

class TestOpenAICompatibleEndpointCallFunction(unittest.TestCase):
    @patch('openai.OpenAI')
    def test_call_function_success_and_error(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        endpoint = OpenAICompatibleEndpoint("model-id", SystemPrompt())

        # Create a dummy tool that returns a known result
        root_param = ToolParam(type="object", name="params", property=[])
        dummy_tool = Tool(
            name="my_tool",
            description="returns hello",
            root_param=root_param,
            func=lambda **kwargs: "hello"
        )
        endpoint.tools = [dummy_tool]

        # Successful tool call
        successful_call = ToolRequest(
            message=None,
            raw_tool_call=make_tool_call(
                id_="success-1",
                name="my_tool",
                arguments=json.dumps({})
            )
        )
        msg_success = endpoint.__call_function__(successful_call, tool_use_callback=None)
        self.assertEqual(msg_success.role, "tool")
        self.assertEqual(msg_success.content, "hello")
        self.assertEqual(msg_success.call_id, "success-1")
        self.assertEqual(msg_success.name, "my_tool")

        # Unsuccessful tool call (tool not found)
        unknown_call = ToolRequest(
            message=None,
            raw_tool_call=make_tool_call(
                id_="fail-1",
                name="unknown_tool",
                arguments=json.dumps({})
            )
        )
        callback = DummyCallback()
        msg_fail = endpoint.__call_function__(unknown_call, tool_use_callback=callback)
        self.assertEqual(msg_fail.role, "tool")
        self.assertEqual(msg_fail.content, "[ERROR] - Tool not found")
        self.assertEqual(msg_fail.call_id, "fail-1")
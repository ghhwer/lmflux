import unittest
from unittest.mock import Mock
from lmflux.core.components import SystemPrompt, Conversation
from lmflux.flow.definitions import DefinedAgent, AgentDefinition
from lmflux.core.llm_impl import EchoLLM
from lmflux.flow.toolbox import ToolBox
from lmflux.agents.sessions import Session
from lmflux.agents.structure import Agent
from lmflux.flow import create_agent, tool

class TestDefinedAgent(unittest.TestCase):
    def test_init(self):
        llm = EchoLLM("llm_id", SystemPrompt())
        agent = DefinedAgent(llm, "agent_id", ToolBox())
        self.assertIsNotNone(agent)

class TestAgentDefinition(unittest.TestCase):
    def test_init(self):
        llm = EchoLLM("llm_id", SystemPrompt())
        definition = AgentDefinition(llm, "agent_id")
        self.assertIsNotNone(definition)

    def test_build(self):
        llm = EchoLLM("llm_id", SystemPrompt())
        definition = AgentDefinition(llm, "agent_id")
        agent = definition.build()
        self.assertIsInstance(agent, DefinedAgent)


def some_tool_callback(agent: Agent, tool_call, result, session: Session):
    pass

def some_conversation_callback_function_bad(agent: Agent,):
    pass

def some_conversation_callback_function(agent: Agent, conversation: Conversation, session: Session):
    pass

def some_badly_defined(agent: Agent):
    pass

@tool
def some_tool(a: str):
    "aa"
    pass

class TestAgentE2E(unittest.TestCase):
    def test_agent_e2e(self):
        llm = EchoLLM("llm_id", SystemPrompt())
        agent = (
            create_agent(llm, 'test-agent')
                .with_conversation_update_callbacks(some_conversation_callback_function)
                .with_tool_update_callbacks(some_tool_callback)
                .with_tools(some_tool)
                .build()
        )
        agent.reset_agent_state()

    def test_agent_e2e_bad_def(self):
        llm = EchoLLM("llm_id", SystemPrompt())
        with self.assertRaises(AttributeError) as cm:
            agent = (
                create_agent(llm, 'test-agent')
                    .with_conversation_update_callbacks(some_conversation_callback_function_bad)
                    .build()
            )
        self.assertIn('must be defined as', str(cm.exception))


if __name__ == '__main__':
    unittest.main()
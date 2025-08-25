import unittest
from unittest.mock import Mock
from lmflux.core.components  import Tool, Message, SystemPrompt
from lmflux.core.llms import LLMModel
from lmflux.core.llm_impl import EchoLLM
from lmflux.agents.structure import Agent
from lmflux.agents.sessions import Session

class NopAgent(Agent):
    def reset_agent_state():
        pass

    def get_tools(self) -> list[Tool]:
        return []
        
    def initialize(self) -> tuple[LLMModel, str]:
        sp = SystemPrompt()
        return EchoLLM("nop_agent", sp, None), "nop_agent"
    
    def add_tool(self, tool:Tool):
        pass
    
    def tool_callback(self, tool_call, result, session: Session):
        pass

class TestAgent(unittest.TestCase):
    def test_init(self):
        agent = NopAgent()
        self.assertIsNotNone(agent.agent_id)

    def test_get_tools(self):
        agent = NopAgent()
        # Mock get_tools method
        self.assertEqual(agent.get_tools(), [])

    def test_initialize(self):
        agent = NopAgent()
        # Mock initialize method
        with unittest.mock.patch.object(agent, 'initialize', return_value=(object(), 'test_id')):
            self.assertEqual(agent.agent_id, 'nop_agent')

    def test_conversate_and_log_step(self):
        agent = NopAgent()
        session = Session()
        message = agent.conversate(
            Message('user', 'something'), session
        )
        agent.log_agent_step(
            session,
            "Testing Step",
            [message],
            True
        )
        
if __name__ == '__main__':
    unittest.main()
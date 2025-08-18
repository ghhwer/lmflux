from lmflux.core.llms import LLMModel
from lmflux.core.components import Tool
from lmflux.agents.structure import Agent
from lmflux.flow.toolbox import ToolBox

class DefinedAgent(Agent):
    def __init__(
        self, 
        llm: LLMModel,
        agent_id: str,
        toolbox:ToolBox
    ):
        self.llm = llm
        self.agent_id = agent_id
        self.toolbox = toolbox
        super().__init__()
    
    def add_tools(self, *tools:Tool):
        self.toolbox.__add_tools__(*tools)
    
    def add_tool(self, tool:Tool):
        self.toolbox.__add_tool__(tool)
        
    def add_conversation_update_callbacks(self, *funcs:callable, validate_only=False):
        for func in funcs:
            self.add_conversation_update_callback(func, validate_only=validate_only)
    
    def add_tool_callbacks(self, *funcs:callable, validate_only=False):
        for func in funcs:
            self.add_tool_callback(func, validate_only=validate_only)
        
    
    def get_tools(self) -> list[Tool]:
        if (self.toolbox):
            return self.toolbox.tools
        else:
            return []
    
    def reset_agent_state(self,):
        self.llm.reset_state()
    
    def initialize(self,) -> tuple[LLMModel, str]:
        return self.llm, self.agent_id

class AgentDefinition:
    def __init__(self, llm:LLMModel, agent_id:str):
        self.agent = DefinedAgent(
            llm,
            agent_id,
            ToolBox()
        )

    def with_tools(self, *tools:callable) -> 'AgentDefinition':
        self.agent.add_tool(*tools)
        return self
    
    def with_conversation_update_callbacks(self, *callbacks:callable) -> 'AgentDefinition':
        self.agent.add_conversation_update_callbacks(*callbacks, validate_only=True)
        self.agent.add_conversation_update_callbacks(*callbacks, validate_only=False)
        return self
    
    def with_tool_update_callbacks(self, *callbacks:callable) -> 'AgentDefinition':
        self.agent.add_tool_callbacks(*callbacks, validate_only=True)
        self.agent.add_tool_callbacks(*callbacks, validate_only=False)
        return self
    
    def build(self):
        return self.agent

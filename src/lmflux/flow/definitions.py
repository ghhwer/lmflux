from lmflux.core.llms import LLMModel
from lmflux.core.components import Tool, Conversation
from lmflux.agents.sessions import Session
from lmflux.agents.structure import Agent
from lmflux.flow.toolbox import ToolBox
from lmflux.utils.signature_checker import check_compatible

import inspect

EXPECTED_TOOL_CALLBACK_SIGNATURE = [
    {'name': 'agent', 'type': Agent, 'position': 0},
    {'name': 'tool_call', 'type': None, 'position': 1},
    {'name': 'result', 'type': None, 'position': 2},
    {'name': 'session', 'type': Session, 'position': 3}
]
EXPECTED_ACT_SIGNATURE = [
    {'name': 'agent', 'type': Agent, 'position': 0},
    {'name': 'session', 'type': Session, 'position': 1}
]
EXPECTED_CONVERSATION_UPDATE_SIGNATURE = [
    {'name': 'agent', 'type': Agent, 'position': 0},
    {'name': 'conversation', 'type':Conversation , 'position': 1}
]

def empty_act(agent:Agent, session:Session):
    pass

def default_act(agent: Agent, session:Session):
    pass

def default_tool_callback(agent: Agent, tool_call, result, session: Session):
    pass

def default_conversation_callback_function(agent: Agent, conversation: Conversation):
    pass

class DefinedAgent(Agent):
    def __init__(
        self, 
        llm: LLMModel,
        agent_id: str,
        toolbox:ToolBox, 
        pre_act_function:callable, 
        post_act_function: callable,
        act_function: callable,
        tool_callback_function: callable,
        conversation_callback_function: callable
    ):
        self.llm = llm
        self.agent_id = agent_id
        self.toolbox = toolbox
        self.pre_act_func = pre_act_function
        self.post_act_func = post_act_function
        self.act_func = act_function
        self.tool_callback_func = tool_callback_function
        self.conversation_callback_function = conversation_callback_function
        if self.conversation_callback_function:
            self.conversation_callback_function_lambda = lambda conversation: conversation_callback_function(self, conversation)
            self.llm.set_conversation_update_callback(
                self.conversation_callback_function_lambda
            )
        super().__init__()
        
    def get_tools(self) -> list[Tool]:
        if (self.toolbox):
            return self.toolbox.tools
        else:
            return []
    
    def reset_agent_state(self,):
        self.llm.reset_state()
    
    def initialize(self, tools:list[Tool]) -> tuple[LLMModel, str]:
        self.llm.add_tools(tools)
        return self.llm, self.agent_id

    def pre_act(self, session: Session):
        return self.pre_act_func(self, session)
    
    def post_act(self, session: Session):
        return self.post_act_func(self, session)
    
    def act(self, session: Session):
        self.pre_act(session)
        result = self.act_func(self, session)
        self.post_act(session)
        return result

    def tool_callback(self, tool_call, result, session: Session):
        return self.tool_callback_func(self, tool_call, result, session)

class AgentDefinition:
    def __init__(self, llm:LLMModel, agent_id:str):
        self.llm = llm
        self.agent_id = agent_id
        self.toolbox = ToolBox()
        self.pre_act_function = empty_act
        self.post_act_function = empty_act
        self.custom_act_function = default_act
        self.tool_callback_function = default_tool_callback
        self.conversation_callback_function = default_conversation_callback_function

    def with_tools(self, *tools:callable):
        self.toolbox.__add_tools__(*tools)
        return self
    
    def with_pre_act(self, pre_act_function:callable):
        self.pre_act_function = check_compatible(
            pre_act_function, "Pre Act",
            EXPECTED_ACT_SIGNATURE
        )
        return self
    
    def with_post_act(self, post_act_function:callable):
        self.post_act_function = check_compatible(
            post_act_function, "Post Act",
            EXPECTED_ACT_SIGNATURE
        )
        return self
    
    def with_act(self, custom_act_function:callable):
        self.custom_act_function = check_compatible(
            custom_act_function, "Custom Act", 
            EXPECTED_ACT_SIGNATURE
        )
        return self

    def with_tool_callback(self, tool_callback:callable):
        self.tool_callback_function = check_compatible(
            tool_callback, "Tool Callback", 
            EXPECTED_TOOL_CALLBACK_SIGNATURE
        )
        return self
    
    def with_conversation_update_callback(self, conversation_update_callback:callable):
        self.conversation_callback_function = check_compatible(
            conversation_update_callback, "Conversation Update Callback", 
            EXPECTED_CONVERSATION_UPDATE_SIGNATURE
        )
        return self
    
    def build(self):
        return DefinedAgent(
            self.llm,
            self.agent_id,
            self.toolbox,
            self.pre_act_function,
            self.post_act_function,
            self.custom_act_function,
            self.tool_callback_function,
            self.conversation_callback_function
        )

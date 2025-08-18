from abc import ABC, abstractmethod
from lmflux.core.llms import LLMModel
from lmflux.core.components import Conversation
from lmflux.core.components import Message, Tool
from lmflux.agents.components import AgentRef
from lmflux.agents.sessions import Session
from lmflux.utils.signature_checker import check_compatible


class Agent(ABC):
    def __init__(self,):
        self.llm, self.agent_id = self.initialize()
        self.agent_ref = AgentRef(self.agent_id, self)
        self.tool_callbacks, self.conversation_update_callbacks = [], []

    @abstractmethod
    def reset_agent_state(): pass

    @abstractmethod
    def get_tools(self) -> list[Tool]: pass
        
    @abstractmethod
    def initialize(self) -> tuple[LLMModel, str]: pass
    
    @abstractmethod
    def add_tool(self, tool: Tool): pass
    
    def tool_callback(self, tool_call, result, session: Session):
        for callback in self.tool_callbacks:
            callback(self, tool_call, result, session)
    
    def conversation_update_callback(self, conversation:Conversation, session: Session): 
        for callback in self.conversation_update_callbacks:
            callback(self, conversation, session)
            
    def add_conversation_update_callback(self, func:callable, validate_only=False):
        check_compatible(
            func, "Conversation Callback", 
            EXPECTED_CONVERSATION_UPDATE_SIGNATURE
        )
        if not validate_only:
            self.conversation_update_callbacks.append(func)
    
    def add_tool_callback(self, func: callable, validate_only=False):
        check_compatible(
            func, "Tool Callback", 
            EXPECTED_TOOL_CALLBACK_SIGNATURE
        )
        if not validate_only:
            self.tool_callbacks.append(func)
    
    def reset_state(self,):
        self.llm.reset_state()
    
    def conversate(self, message:Message, session: Session) -> Message:
        tool_callback = lambda tool_call, result: self.tool_callback(tool_call, result, session)
        conversation_update_callback = lambda conversation: self.conversation_update_callback(conversation, session)
        self.llm.set_conversation_update_callback(conversation_update_callback)
        self.llm.tools = self.get_tools()
        data = self.llm.chat(message, tool_use_callback=tool_callback)
        return data
    
    def log_agent_step(self, session:Session, step_message: str, messages:list[Message], print_full_message=False):
        messages_log = '\n'.join([str(message) for message in messages])
        full_log = f'({self.agent_id}) {step_message}'
        if print_full_message:
            full_log  += f'\n-----\n{messages_log}\n-----\n'
        session.logger.info(full_log)

EXPECTED_TOOL_CALLBACK_SIGNATURE = [
    {'name': 'agent', 'type': Agent, 'position': 0},
    {'name': 'tool_call', 'type': None, 'position': 1},
    {'name': 'result', 'type': None, 'position': 2},
    {'name': 'session', 'type': Session, 'position': 3}
]
EXPECTED_CONVERSATION_UPDATE_SIGNATURE = [
    {'name': 'agent', 'type': Agent, 'position': 0},
    {'name': 'conversation', 'type':Conversation , 'position': 1},
    {'name': 'session', 'type': Session, 'position': 2}
]
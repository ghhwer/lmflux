from lmflux.agents.sessions import Session
from lmflux.agents.structure import Agent
from lmflux.agents.components import Context

from lmflux.core.components import Tool, ToolParam, Message, Conversation, ToolRequest
from lmflux.utils.signature_checker import check_compatible

from lmflux.graphs.base.graph import NodeDefinition, Graph, NodeGroupDefinition
from lmflux.graphs.mesh.markdown_renderer import MarkdownRenderer
from lmflux.graphs.mesh.mermaid_renderer import MermaidRender
from lmflux.graphs.mesh.result_renderer import MeshResultRenderer

from uuid import uuid4
import networkx as nx

EXPECTED_TRANSFORMER_CALLBACK = [
    {'name': 'session', 'type': Session, 'position': 0}
]
EXPECTED_AGENTIC_CALLBACK = [
    {'name': 'agent', 'type': Agent, 'position': 0},
    {'name': 'session', 'type': Session, 'position': 1}
]

class TransformerMeshNode(NodeDefinition):
    def __init__(self, name: str):
        super().__init__(name)
    
    def defines_sub_graph(self) -> bool:
        return False

class AgenticNode(NodeDefinition):
    agent:Agent
    
    def __init__(self, name: str, agent: Agent):
        super().__init__(name)
        self.agent = agent
    
    def defines_sub_graph(self) -> bool:
        return False

def ask_agent(query, agent_a:Agent, agent_b:Agent, graph_class:'MeshGraph'):
    trace_id = str(uuid4())
    query_message = Message(
        "user", query
    )
    response = agent_b.conversate(query_message, graph_class.session)
    # Call the callback
    graph_class.__attach_agent_response_on_trace_id__(agent_a, agent_b, query, query_message, response, trace_id)
    return {"response": response.content, "__trace_id": trace_id}

def agent_conversation_update_callback(agent:Agent, conversation: Conversation, session: Session):
    if session.get('show_progress'):
        mg: 'MeshGraph' = session.get('__mesh_graph')
        mg.show_result()

def agent_tool_callback(agent: Agent, tool_call:ToolRequest, result, session:Session):
    mg: 'MeshGraph' = session.get('__mesh_graph')
    if mg:
        if type(result) == dict:
            tid = result.get('__trace_id')
            if tid:
                mg.__attach_agent_request_on_trace_id__(agent, tool_call, result, tid)

def _indent_prefix(depth: int) -> str:
    return ("\t" * (depth-1)) + "- "


class MeshGraph(Graph):
    # -------------
    #  Private methods 
    # -------------
    
    def __init__(self):
        super().__init__()
        self.conversation_graph = nx.DiGraph()
        self.built = False
        self.mesh_hash = None
        self.agent_interactions = {}
        self.user_interactions = []
        self.renderer = MarkdownRenderer(self)
        self.is_markdown = True
        self.is_mermaid = True

    def __make_hash__(self,) -> str:
        pass
    
    def __create_agentic_node__(self, agent:Agent):
        agent.add_conversation_update_callback(agent_conversation_update_callback)
        return AgenticNode(
            agent.agent_id,
            agent
        )
    
    def __attach_agent_request_on_trace_id__(
        self, agent_a: Agent, 
        tool_call:ToolRequest, result:str, 
        trace_id: str
    ):
        self.agent_interactions[trace_id].update(
            {
                "agent_a_metadata": {
                    "request_message_id": tool_call.message.message_id
                }
            }
        )
    
    def __attach_agent_response_on_trace_id__(
        self, agent_a: Agent, agent_b: Agent, query:str, 
        starting_message:Message, response_message:Message,
        trace_id: str
    ):
        self.agent_interactions[trace_id] = {
            "interaction_id": trace_id,
            "agent_a_id": agent_a.agent_id,
            "agent_b_id": agent_b.agent_id,
            "query": query,
            "agent_b_metadata":{
                "request_message_id": starting_message.message_id,
                "response_message_id":response_message.message_id
            }
        }
    
    def __clear_state__(self,):
        self.session = Session()
        self.session.set("__mesh_graph", self)
        self.agent_interactions = {}
        self.user_interactions = []
        for node in self.G.nodes(data=True):
            node_definition: AgenticNode = node[-1].get("obj")
            node_definition.agent.reset_state()
    
    # -------------
    #  Public API 
    # -------------
    def add_agent(self, agent: Agent):
        self.__add_node__(
            self.__create_agentic_node__(agent)
        )
        
    def connect_agents(self, agent_a: Agent, agent_b: Agent, relationship_description:str):
        definition_a = self.__find_object_in_graph_by_name__(agent_a.agent_id)
        definition_b = self.__find_object_in_graph_by_name__(agent_b.agent_id)
        
        if not definition_a:
            definition_a = self.__create_agentic_node__(agent_a)
            self.__add_node__(definition_a)
        if not definition_b:
            definition_b = self.__create_agentic_node__(agent_b)
            self.__add_node__(definition_b)
        
        query = ToolParam("str", "query", is_required="true")
        root_param = ToolParam(
            type="object",
            name="parameters",
            property=[query]
        )
        tool = Tool(
            f"talk_to_{agent_b.agent_id}", relationship_description, root_param,
            func=lambda query: ask_agent(query, agent_a, agent_b, self)
        )
        agent_a.add_tool(tool)
        agent_a.add_tool_callback(agent_tool_callback)
        _metadata = {"relationship_description": relationship_description, "label":"Can call"}
        self.__add_edge__(definition_a, definition_b, _metadata=_metadata)
    
    def query_agent(self, agent: Agent, query: str, clear=True, show_progress=False):
        if clear:
            self.__clear_state__()
        
        self.session.set("show_progress", show_progress)
        
        message = Message(
            "user", query
        )
        self.user_interactions.append({
            "interaction_id": str(uuid4()),
            "agent_id": agent.agent_id,
            "response_message_id": None,
            "response_content": None,
            "request_message_id": message.message_id,
            "request_content": message.content
        })

        response = agent.conversate(message, self.session)
        self.user_interactions[-1] = {
            "interaction_id": str(uuid4()),
            "agent_id": agent.agent_id,
            "response_message_id": response.message_id,
            "response_content": response.content,
            "request_message_id": message.message_id,
            "request_content": message.content
        }
        if self.session.get("show_progress_as_graph"):
            self.__show_meramaid__()
        elif self.session.get("show_progress_as_text"):
            self.__log_progress__()

        return response

    def set_markdown_render(self):
        self.renderer = MarkdownRenderer(self)
    
    def set_mermaid_render(self):
        self.renderer = MermaidRender(self)

    def show_result(self,):
        self.renderer.render()
    
def transformer_node(func:callable):
    """
    Decorator for creating an TransformerTask.

    Usage:
        @transformer_task
        def my_task(session: Session):
            ...
    """
    check_compatible(func, "run", EXPECTED_TRANSFORMER_CALLBACK)
    return TransformerMeshNode(func.__name__, func)

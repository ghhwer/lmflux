from lmflux.agents.sessions import Session
from lmflux.agents.structure import Agent
from lmflux.agents.components import Context

from lmflux.graphs.base.graph import NodeDefinition, Graph, NodeGroupDefinition
from lmflux.utils.signature_checker import check_compatible

import networkx as nx
from abc import abstractmethod

EXPECTED_TRANSFORMER_CALLBACK = [
    {'name': 'session', 'type': Session, 'position': 0}
]
EXPECTED_AGENTIC_CALLBACK = [
    {'name': 'agent', 'type': Agent, 'position': 0},
    {'name': 'session', 'type': Session, 'position': 1}
]

class RunnableNodeDefinition(NodeDefinition):
    def __execute__(self, session: Session):
        self.pre_run(session)
        self.run(session)
        self.post_run(session)
    @abstractmethod
    def pre_run(self, session: Session) -> None:
        ...
    @abstractmethod
    def post_run(self, session: Session) -> None:
        ...
    @abstractmethod
    def run(self, session: Session) -> None:
        ...
    
class TransformerTask(RunnableNodeDefinition):
    def __init__(self, name: str, run_callback:callable):
        super().__init__(name)
        self.run_callback = check_compatible(run_callback, "run", EXPECTED_TRANSFORMER_CALLBACK)
    def defines_sub_graph(self) -> bool:
        return False
    def pre_run(self, session: Session) -> None:
        pass
    def post_run(self, session: Session) -> None:
        pass
    def run(self, session: Session) -> None:
        self.run_callback(session)

class AgenticTask(RunnableNodeDefinition):
    def __init__(self, name: str, agent: Agent, run_callback:callable):
        super().__init__(name)
        self.agent = agent
        self.run_callback = check_compatible(run_callback, "run", EXPECTED_AGENTIC_CALLBACK)
    def defines_sub_graph(self) -> bool:
        return False
    def pre_run(self, session: Session) -> None:
        pass
    def post_run(self, session: Session) -> None:
        pass
    def run(self, session: Session) -> None:
        self.run_callback(self.agent, session)

class TaskGraph(Graph):
    # -------------
    #  Private methods 
    # -------------
    def __init__(self):
        super().__init__(draw_labels_around=True)
    
    # -------------
    #  Public API 
    # -------------
    
    def run(self, with_context:Context=None) -> Session:
        """
        Execute every node of the graph respecting the directed edges.
        Cycles raise a ``RuntimeError``.
        """
        if with_context:
            session=Session(with_context)
        else:
            session = Session()
        try:
            order = list(nx.topological_sort(self.G))
        except nx.NetworkXUnfeasible as exc:  # pragma: no cover
            raise RuntimeError(
                "The task graph contains a cycle and cannot be executed."
            ) from exc

        for nid in order:
            obj: RunnableNodeDefinition = self.G.nodes[nid]["obj"]
            if not isinstance(obj, RunnableNodeDefinition):
                raise RuntimeError(
                    f"Node {nid} is not of type RunnableNodeDefinition."
                )
            obj.__execute__(session)
        return session

    def connect_tasks(self, task_a:RunnableNodeDefinition, task_b:RunnableNodeDefinition):
        definition_a = self.__find_object_in_graph_by_name__(task_a.name)
        definition_b = self.__find_object_in_graph_by_name__(task_b.name)
        
        if not definition_a:
            self.__add_node__(task_a)
        if not definition_b:
            self.__add_node__(task_b)

        _metadata = {}
        self.__add_edge__(task_a, task_b, _metadata=_metadata)

# -------------
#  Decorators
# -------------
def transformer_task(func:callable):
    """
    Decorator for creating an TransformerTask.

    Usage:
        @transformer_task
        def my_task(session: Session):
            ...
    """
    check_compatible(func, "run", EXPECTED_TRANSFORMER_CALLBACK)
    return TransformerTask(func.__name__, func)

def agentic_task(agent: Agent):
    """
    Decorator for creating an AgenticTask with a specific agent.

    Usage:
        @agentic_task(my_agent)
        def my_task(agent: Agent, session: Session):
            ...
    """
    def decorator(func: callable):
        check_compatible(func, "run", EXPECTED_AGENTIC_CALLBACK)
        return AgenticTask(func.__name__, agent, func)
    return decorator
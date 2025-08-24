from abc import abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # executed only by type checkers, not at runtime
    from lmflux.graphs.mesh.definitions import MeshGraph

class MeshResultRenderer():
    def __init__(self, G:'MeshGraph'):
        self.G = G
    
    def  __make_interactions_map__(self):
        G = self.G
        messages = [
            {
                "actor": node[-1].get("obj").agent.agent_id,
                "messages":[
                    message
                    for message in node[-1].get("obj").agent.llm.conversation
                ],
                "incoming_interactions_cross_agent":[
                    x
                    for _, x in G.agent_interactions.items() if x.get("agent_b_id") == node[-1].get("obj").agent.agent_id
                ],
                "outgoing_interactions_cross_agent":[
                    x
                    for _, x in G.agent_interactions.items() if x.get("agent_a_id") == node[-1].get("obj").agent.agent_id
                ]
            }
            for node in G.G.nodes(data=True)
        ]
        user_interactions = G.user_interactions
        return (messages, user_interactions)
    
    @abstractmethod
    def render(self,): ...
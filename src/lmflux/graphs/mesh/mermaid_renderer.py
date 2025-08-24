import itertools
from typing import TYPE_CHECKING

from lmflux.graphs.mesh.result_renderer import MeshResultRenderer
from lmflux.graphs.utils import show_markdown, IPYTHON_AVAILABLE

if TYPE_CHECKING:  # executed only by type checkers, not at runtime
    from lmflux.graphs.mesh.definitions import MeshGraph
    
def short_id(prefix, counter):
    return f"{prefix}{counter}"

class MermaidRender(MeshResultRenderer):
    def build_mesh_response_meramid(self,):
        messages, user_interactions = self.__make_interactions_map__()
        msg_counter = itertools.count()
        interaction_ids = set()
        global_interaction_edges = []                # edges drawn after all sub-graphs
        actor_agent_message_id_map = {}
        graph_lines = ["flowchart TB"]                # top-to-bottom layout

        graph_lines.append('    %% Global wrapper for all agents')
        graph_lines.append('    subgraph ALL_AGENTS["All Agents"]')
        graph_lines.append('        direction TB')

        for actor_map in messages:
            agent_name = actor_map.get("actor")
            subgraph_name = f'subgraph_{agent_name}'
            graph_lines.append(f'        subgraph {subgraph_name}["{agent_name}"]')
            #graph_lines.append('            style {} fill:#eef,stroke:#333'.format(subgraph_name))
            
            actor_agent_message_id_map[agent_name] = {}

            previous_msg_id = None
            # ------------------------------------------------------------------
            # Agent's own messages
            # ------------------------------------------------------------------
            for msg in actor_map.get("messages", []):
                short_msg_id = short_id('msg', next(msg_counter))
                actor_agent_message_id_map[agent_name][msg.message_id] = short_msg_id
                # Store the mapping if you later need the original IDs for debugging
                # (optional, not printed in the diagram)
                # original_to_short[msg.message_id] = short_msg_id

                graph_lines.append(f'            {short_msg_id}["{msg.role}"]')
                # connect sequential messages within the same agent
                if previous_msg_id:
                    graph_lines.append(f'            {previous_msg_id} --> {short_msg_id}')
                previous_msg_id = short_msg_id

            # ------------------------------------------------------------------
            # Cross-agent interactions (both incoming & outgoing)
            # ------------------------------------------------------------------
            # Incoming - other agents talk *to* this one
            for intc in actor_map.get("incoming_interactions_cross_agent", []):
                int_id = intc['interaction_id']
                interaction_ids.add(int_id)

                # Draw a small rounded-box node for the interaction
                int_node_id = f'{int_id}__in'
                int_label = f'talk to {intc["agent_a_id"]}'
                graph_lines.append(f'            {int_node_id}((\"{int_label}\"))')
                # Edge from request message (inside this agent) to the interaction node
                req_msg = intc.get('agent_b_metadata', {}).get('request_message_id')
                res_msg = intc.get('agent_b_metadata', {}).get('response_message_id')
                if req_msg:
                    req_msg_short_id = actor_agent_message_id_map[agent_name].get(req_msg, req_msg)
                    res_msg_short_id = actor_agent_message_id_map[agent_name].get(res_msg, res_msg)
                    # Find the short id we generated for this request message
                    # (simple lookup: assumes request_message_id is present in this actor’s messages)
                    # If not found, use the original id - Mermaid will still render it.
                    graph_lines.append(f'            {int_node_id} --> {req_msg_short_id}')
                    graph_lines.append(f'            {res_msg_short_id} --> {int_node_id}')

            # Outgoing - this agent talks *to* another one
            for intc in actor_map.get("outgoing_interactions_cross_agent", []):
                int_id = intc['interaction_id']
                interaction_ids.add(int_id)

                int_node_id = f'{int_id}__out'
                int_label = f'talk to {intc["agent_b_id"]}'
                graph_lines.append(f'            {int_node_id}((\"{int_label}\"))')
                req_msg = intc.get('agent_a_metadata', {}).get('request_message_id')
                if req_msg:
                    req_msg_short_id = actor_agent_message_id_map[agent_name].get(req_msg, req_msg)
                    graph_lines.append(f'            {req_msg_short_id} --> {int_node_id}')

                global_interaction_edges.append(
                    f'{int_id}__out <-.-> {int_id}__in'
                )
            graph_lines.append('        end')          # close agent sub-graph
        graph_lines.append('    end')                # close ALL_AGENTS wrapper

        # ------------------------------------------------------------------
        # Add a wrapper for the human (user) - place it before the ALL_AGENTS sub-graph
        # ------------------------------------------------------------------
        graph_lines.append('    %% Global wrapper for humans')
        human_subgraph = 'subgraph_human["Human"]'
        graph_lines.append( f'    subgraph {human_subgraph}')
        #graph_lines.append( '        style subgraph_human fill:#ffe,stroke:#333')
        # We'll store short ids for the human messages in a temporary dict
        human_msg_map = {}
        for ui in user_interactions:
            # human request node
            human_req_id = short_id('hmsg', next(msg_counter))
            human_res_id = short_id('hmsg', next(msg_counter))
            
            human_msg_map[ui['response_message_id']] = human_res_id
            human_msg_map[ui['request_message_id']] = human_req_id
            graph_lines.append(f'        {human_req_id}["User Query"]')
            graph_lines.append(f'        {human_res_id}["User Response"]')
            
            req_agent_id = actor_agent_message_id_map[ui['agent_id']][ui['request_message_id']]
            res_agent_id = actor_agent_message_id_map[ui['agent_id']][ui['response_message_id']]
            
            global_interaction_edges.append(f'        {human_req_id} -.-> {req_agent_id}')
            global_interaction_edges.append(f'        {res_agent_id} -.-> {human_res_id}')
            
        # close the human sub-graph (after all agents are processed)
        graph_lines.append('    end')   # close Human wrapper

        # ----------------------------------------------------------------------
        # Optional styling for interaction nodes
        # ----------------------------------------------------------------------
        #graph_lines.append('    classDef interaction fill:#f9f9f9,stroke:#555')
        graph_lines.append('    class ' + ', '.join(
            f'{iid}__in' for iid in interaction_ids) + ' interaction')
        graph_lines.append('    class ' + ', '.join(
            f'{iid}__out' for iid in interaction_ids) + ' interaction')


        # ----------------------------------------------------------------------
        # Global cross-agent interaction edges (drawn only once)
        # ----------------------------------------------------------------------
        graph_lines.extend(global_interaction_edges)
        # ----------------------------------------------------------------------
        # Produce final Mermaid source
        # ----------------------------------------------------------------------
        mermaid_chart = "\n".join(graph_lines)
        return mermaid_chart
    
    def render(self):
        show_markdown(f"```mermaid\n{self.build_mesh_response_meramid()}\n```")
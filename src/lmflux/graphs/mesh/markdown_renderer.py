from typing import TYPE_CHECKING
from collections import defaultdict
from typing import List, Dict

from lmflux.graphs.mesh.result_renderer import MeshResultRenderer
from lmflux.graphs.utils import show_markdown, IPYTHON_AVAILABLE

if TYPE_CHECKING:  # executed only by type checkers, not at runtime
    from lmflux.graphs.mesh.definitions import MeshGraph
    
def indent_prefix(depth: int) -> str:
    return ("\t" * (depth-1)) + "- "

class MarkdownRenderer(MeshResultRenderer):
    def build_markdown_log(self) -> str:
        messages, user_interactions = self.__make_interactions_map__()
        # --------------------------------------------------------------
        # Build quick look‑ups: message_id → agent  &  agent → #messages
        # --------------------------------------------------------------
        msg_to_agent: Dict[str, str] = {}
        agent_msg_counts: Dict[str, int] = defaultdict(int)

        for actor_map in messages:
            agent_name = actor_map.get("actor")
            for msg in actor_map.get("messages", []):
                # every message object is expected to have a ``message_id`` attribute
                msg_id = getattr(msg, "message_id", None)
                if not msg_id:
                    continue          # skip malformed entries
                msg_to_agent[msg_id] = agent_name
                agent_msg_counts[agent_name] += 1

        # --------------------------------------------------------------
        # Build the *call graph*: who calls whom?
        # --------------------------------------------------------------
        calls: Dict[str, List[str]] = defaultdict(list)

        for actor_map in messages:
            src_agent = actor_map.get("actor")

            # Outgoing → the *target* agent
            for out_int in actor_map.get("outgoing_interactions_cross_agent", []):
                tgt = out_int.get("agent_b_id")
                if tgt:
                    calls[src_agent].append(tgt)

            # Incoming is the opposite direction of someone else’s outgoing
            for inc_int in actor_map.get("incoming_interactions_cross_agent", []):
                src_of_inc = inc_int.get("agent_a_id")
                if src_of_inc:
                    calls[src_of_inc].append(src_agent)

        # --------------------------------------------------------------
        # Render the hierarchy
        # --------------------------------------------------------------
        lines: List[str] = []

        # ----- Human header -------------------------------------------------
        human_queries = [
            ui.get("request_content", "").strip()
            for ui in user_interactions
            if ui.get("request_content")
        ]
        lines.append("**Human**:")
        lines.append("")
        lines.append(("".join(human_queries) if human_queries else ""))
        
        # ----- Depth‑first walk (global visited set prevents double prints) -----
        visited_global: set = set()          # never render the same agent twice

        def _walk(agent: str, depth: int, visited_local: set) -> None:
            """
            Recursive DFS.
            * `visited_local` protects against cycles *inside* the current branch.
            * `visited_global` guarantees a name is printed only once, even if it
                appears as a root of another human request.
            """
            # If we have already printed this agent somewhere else, stop.
            if agent in visited_global:
                return

            # ---- print the current line ---------------------------------
            prefix = indent_prefix(depth)
            cnt = agent_msg_counts.get(agent, 0)
            lines.append(f"{prefix}{agent} ({cnt} message{'s' if cnt != 1 else ''})")
            visited_global.add(agent)

            # ---- recurse to children ------------------------------------
            for child in calls.get(agent, []):
                if child in visited_local:          # local cycle -> skip
                    continue
                visited_local.add(child)
                _walk(child, depth + 1, visited_local)
                visited_local.remove(child)         # back‑track

        # Each user interaction may start a *different* root agent.
        lines.append("")
        lines.append("**Agent Calls**")
        lines.append("")
        for ui in user_interactions:
            req_msg_id = ui.get("request_message_id")
            if not req_msg_id:
                continue
            root_agent = msg_to_agent.get(req_msg_id)
            if not root_agent:
                continue
            # Start the walk only if we have never printed this root already.
            if root_agent not in visited_global:
                _walk(root_agent, depth=1, visited_local={root_agent})
        lines.append("")
        # ----- AI footer -------------------------------------------------
        for ui in user_interactions:
            if ui.get("response_content"):
                response = ui.get("response_content").strip()
                lines.append("**AI**:")
                lines.append("")
                lines.append(response)

        # --------------------------------------------------------------
        # Return the assembled text
        # --------------------------------------------------------------
        return "\n".join(lines)
    
    def render(self):
        show_markdown(self.build_markdown_log())
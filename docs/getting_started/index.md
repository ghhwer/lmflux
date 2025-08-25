# Getting Started with **lmflux**

This guide walks you through the core concepts of **lmflux**—tools, agents, sessions, graphs, and templated prompts—using runnable snippets taken directly from the example notebooks.

For direct examples go to our [github repository](https://github.com/ghhwer/lmflux) where you can find notebook examples.

---

## 1.Define Re‑usable Tools

Tools are plain Python functions decorated with `@tool`.  
The decorator turns the return value into a JSON‑serializable payload that agents can invoke.

```python
# tools.py
from lmflux import tool

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return {"result": a + b}
```

> **Tip:** Return a dictionary (or a dataclass that can be serialized) so the LLM can parse the result.

---

## 2.Create an Agent

Agents are instantiated via `openai_agent`. Pass the model name, a friendly identifier, and any tools the agent may use.

```python
# agents.py
from lmflux import openai_agent, tool

# Re‑use the `add` tool defined above
agent = openai_agent(
    name="my‑agent",
    model="openai.gpt_oss_20b",
    tools=[add],
    system_prompt="You are a helpful assistant. Use tools when available."
)
```

---

## 3. Converse with an Agent

A conversation lives inside a `Session`.  
`Message` objects carry a role (`"user"` or `"assistant"`) and text.

```python
# quick_conversation.py
from lmflux import Session, Message

session = Session()
msg = Message("user", "What is 965 + 33264?")
resp = agent.conversate(msg, session)
print(resp.content)   # → 34229
```

---

## Multi‑Agent Setup

The library lets you connect multiple agents so they can collaborate on queries.  
Two graph types are available:

* **MeshGraph** – connects agents for direct message routing.  
* **TaskGraph** – chains data‑transformer and agentic tasks.

For detailed definitions, options, and use‑case examples see the **[Graph Types](graph_types/)** page.

### 4.1. Connect Agents with a **MeshGraph**

A `MeshGraph` lets agents talk to each other.  
Use `connect_agents` to declare a directed edge and a description that becomes the “instruction” for the source agent.

```python
# mesh_demo.py
from lmflux.graphs import MeshGraph

# Assume `peter` and `bob` are agents (see example_agent_mesh.ipynb)
G = MeshGraph()
G.connect_agents(peter, bob, "Ask Bob for employee information.")
G.show_mermaid()                     # visualises the graph

# Query Peter; the graph routes the request to Bob automatically
msg = G.query_agent(peter, "What is the status of employee 123456789?", show_progress=True)
print(msg.content)
```

---

### 4.2. Orchestrate Tasks with a **TaskGraph**

`TaskGraph` strings together **transformer** (pure data) and **agentic** (LLM) tasks.

```python
# task_demo.py
from lmflux.graphs import TaskGraph, transformer_task, agentic_task
from lmflux import Session, Agent

@transformer_task
def set_data(session: Session):
    session.set("a", 985)
    session.set("b", 1265)

@agentic_task(agent)               # `agent` created earlier
def add_task(agent: Agent, session: Session):
    a, b = session.get("a"), session.get("b")
    msg = Message("user", f"What is {a}+{b}?")
    resp = agent.conversate(msg, session)
    session.set("result", resp.content)

G = TaskGraph()
G.connect_tasks(set_data, add_task)
G.show_mermaid()
result_session = G.run()
print(result_session.context["result"])   # → 2250
```

---

## 5. Manage Prompts with **Templates**

The `Templates` class stores, retrieves, and optionally persists prompt templates as markdown files.

```python
# templates_demo.py
from lmflux import Templates, TemplatedPrompt, SystemPrompt

# Store a simple template (in‑memory or on‑disk)
Templates().put_template("greeting", "Hello {{user_name}}!", persistent=True)

# Retrieve and render it
msg = TemplatedPrompt("greeting", role="system")
print(msg.get_message({"user_name": "Boris"}))
# → "Hello Boris!"

# System prompts can also be templated
Templates().put_template(
    "barking_assistant",
    "You are a helpful assistant. Always end your reply with a bark."
)
system = SystemPrompt("barking_assistant")
print(system.get_message())
```

**Persistence options**  

```python
# Set a custom location for persisted templates
Templates().set_location("./examples")
Templates().put_template("my.template", "content", persistent=True)

# Hard delete removes the file from disk
Templates().set_hard_external_delete()
Templates().delete_template("my.template")
```
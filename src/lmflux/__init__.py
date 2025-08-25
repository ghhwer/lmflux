# Core component
from lmflux.core.components import (SystemPrompt, Message, Conversation, LLMOptions, TemplatedPrompt)
from lmflux.core.templates import Templates
from lmflux.core.llm_impl import OpenAICompatibleEndpoint

# Agent components
from lmflux.agents.sessions import Session
from lmflux.agents.structure import Agent
from lmflux.agents.components import Context

# Flow Components
from lmflux.flow import (
    create_agent,
    tool
)


def openai_agent(
    agent_id:str, model_id:str, tools:list[callable]=None, 
    system_prompt="You are a helpful assistant.", 
    options=LLMOptions()
) -> Agent:
    """
    Creates a new OpenAI compatible agent.
    It will use the `OpenAICompatibleEndpoint` as its base LLM, so It will take the OPENAI_API_BASE and OPENAI_API_KEY enviroment variables to create a OAI client.
    
    Args:
    - agent_id (str) : A unique identifier for the agent. It will be used to identify the agent in the conversation.
    - model_id (str) : The ID of the OpenAI model to use.
    - system_prompt (SystemPrompt, optional): The prompt to use as a starting point for the conversation. Defaults to "You are a helpful assistant.".
    - tools (list[callable], optional): A list of functions that will be used by the agent to perform tasks. Defaults to None.
    - options (LLMOptions, optional): Additional options to pass to the LLM. Defaults to LLMOptions().

    Returns:
    - Agent
    """
    llm = OpenAICompatibleEndpoint(model_id, SystemPrompt(content=system_prompt), options=options)
    agent = create_agent(llm, agent_id=agent_id)
    if tools:
        agent.with_tools(*tools)
    return agent.build()

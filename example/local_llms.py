from lmflux.core.llm_impl import OpenAICompatibleEndpoint
from lmflux.core.components import LLMOptions, SystemPrompt

class Llama4Maverick(OpenAICompatibleEndpoint):
    def __init__(self, system_prompt:SystemPrompt, options:LLMOptions=None):
        if options is None:
            options = LLMOptions()
        super().__init__(model_id="us.meta.llama4-maverick-17b-instruct-v1:0", 
                         system_prompt=system_prompt, options=options)

class AmazonNovaMicro(OpenAICompatibleEndpoint):
    def __init__(self, system_prompt:SystemPrompt, options:LLMOptions=None):
        if options is None:
            options = LLMOptions()
        super().__init__(model_id="amazon.nova-micro-v1:0", 
                         system_prompt=system_prompt, options=options)
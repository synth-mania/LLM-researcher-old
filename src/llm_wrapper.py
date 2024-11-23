import openai
from .llm_config import get_llm_config

class LLMWrapper:
    def __init__(self, preset_name):
        """
        Initializes a new instance of the LLMWrapper class.

        This class is used to interact with a large language model (LLM) API.
        It uses the configuration provided by the llm_config module to make requests
        to the LLM API and retrieve responses.
        """
        
        self.llm_config = get_llm_config(preset_name)
        openai.api_key = self.llm_config.get('api_key')
        openai.api_base = self.llm_config.get('base_url', 'http://localhost:1234')
    
    def generate(self, prompt, parameter_override=None):
        """
        Generates a response from the LLM based on the given prompt.

        Args:
            prompt (str): The input prompt for which to generate a response.
            parameter_override (dict): A dictionary of key-value pairs that override
                the default configuration provided by llm_config. Defaults to None.

        Returns:
            str: The generated response from the LLM.
        """

        if parameter_override is None:
            parameter_override = {}

        # Create a new dictionary with all the parameters from get_llm_config, and then update it with any
        # overrides specified in parameter_override
        parameters = self.llm_config.copy()
        parameters.update(parameter_override)

        response = openai.Completion.create(
            prompt=prompt,
            **parameters
        )
        return response.choices[0].text.strip()

class ChatLLMWrapper(LLMWrapper):
    def __init__(self, preset_name, system_message):
        
        super().__init__(preset_name)
        self.system_message = system_message

        self.messages = [{"role": "system", "content": system_message}]

    def generate(self, user_input, parameter_override=None):
        if parameter_override is None:
            parameter_override = {}
        
        # Create a new dictionary with all the parameters from get_llm_config, and then update it with any
        # overrides specified in parameter_override
        parameters = self.llm_config.copy()
        parameters.update(parameter_override)
        
        self.messages.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            message=self.messages
            **parameters
        )
        
        unpacked_response = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": unpacked_response})

        return unpacked_response
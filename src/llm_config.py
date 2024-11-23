import json

def input_default(prompt, default):
    user_input = input(prompt)
    if user_input.strip() == '':
        return default
    else:
        return user_input


def get_llm_config():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("No config file found. Please provide the following parameters to connect to an OpenAI compatible API:")

        api_key = input_default("API Key: ", "")
        base_url = input_default("Base URL: ", "https://localhost:1234")
        timeout = int(input_default("Timeout (seconds): ", 60))
        max_tokens = int(input_default("Max tokens: ", 150))
        
        config = {
            "api_key": api_key,
            "base_url": base_url,
            "timeout": timeout,
            "max_tokens": max_tokens
        }
        
        with open("config.json", "w") as f:
            json.dump(config, f)
            
        return config
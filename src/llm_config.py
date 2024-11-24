import json

def input_default(prompt, default):
    user_input = input(prompt)
    if user_input.strip() == '':
        return default
    else:
        return user_input

def get_llm_config(preset_name = "default"):
    try:
        with open("config/model_presets/"+preset_name+".json", "r") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("No config file found. Please provide the following parameters to connect to an OpenAI compatible API:")

        with open("config/parameter_defaults.json", 'r') as file:
            PARAMETER_DEFAULT = json.load(file)

        config = {}
        for key, default in PARAMETER_DEFAULT.items():
            value = input_default(f"{key}: ", default)
            config[key] = value
        with open("config/model_presets/{preset_name}.json", "w") as f:
            json.dump(config, f)
            
        return config
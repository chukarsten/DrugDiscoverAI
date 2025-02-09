import openai
import subprocess
from local_model_list import local_model_options
from openai import OpenAI

def check_for_local_model(model):
    """
    A function to check the user's local ollama environment and parse the ollama list output to see
    what models they have pulled.

    (base) C:\\Users\\User>ollama list
    NAME               ID              SIZE      MODIFIED
    llama3.2:1b        baf6a787fdff    1.3 GB    About a minute ago
    llama3.2:latest    a80c4f17acd5    2.0 GB    17 minutes ago

    Args:
        model: The string of the model to check if it's local or not.

    Returns:
        Whether the model is local or not.
    """
    stdout = subprocess.run(["ollama", "list"], capture_output=True).stdout.decode('utf-8')
    pulled_models = [stdout.split("\n")[i].split("  ")[0] for i in range(1,len(stdout.split("\n")))]
    pulled_models = [p if "latest" not in p else p.split(":")[0] for p in pulled_models ]
    return True if model in pulled_models else False

def pull_local_model(model):
    if not check_for_local_model(model):
        print(f"{model} not in local cache, downloading.")
        subprocess.run(["ollama", "pull", model])
    else:
        print(f"{model} already downloaded.")

def find_smallest_local_model(available_model_dict):
    smallest_models = [model for model in available_model_dict if available_model_dict[model] == min(available_model_dict.values())]
    smallest_model = None
    if len(smallest_models) == 1:
        smallest_model = smallest_models[0]
    else:
        smallest_model = smallest_models[0]
    return smallest_model

class ModelPicker():
    def __init__(self, model="smallest"):
        if model not in local_model_options or not "smallest":
            raise ValueError(f"Model must be either 'smallest' or {local_model_options.keys()}")
        self.base_model = find_smallest_local_model(local_model_options) if model == "smallest" else "llama3.3"
        self.openai = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.system_prompt = f"You are a small language model based on {self.base_model}  \
            You have a local list of models available and you want to help the user pick \
            one to use.  They can also choose to use their API keys to access an LLM API. \
            First, try to find out if they want to use a local model or access one through an API.\
            If they want to use an API, respond with just the word 'api', but if they want to \
            use a local model, respond with just the string representing the model from {local_model_options.keys()}"
        self.intro_prompt = f"Introduce yourself.  The LLMs the user can use are based in \
            the keys of this python dictionary {local_model_options}. The values of that \
            dictionary are the integer number of parameters of the respective model, in \
            billions, that the model contains.  Make sure the user doesn't pick a model \
            too big for their system memory."
        pull_local_model(self.base_model)
        self.messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.intro_prompt}
        ]

    def decide_on_model(self):
        response = self.openai.chat.completions.create(model=self.base_model, messages=self.messages).choices[0].message.content
        print(response)
        self.app_assistant_message(response)
        while response not in ["api"] + local_model_options.keys():
            user_message = input("Well?")
            self.app_user_message(user_message)
            response = self.openai.chat.completions.create(model=self.base_model, messages=self.messages).choices[0].message.content
            print(response)
        return response

    def app_assistant_message(self, message):
        self.messages.append({"role": "assistant", "content": message})

    def app_user_message(self, message):
        self.messages.append({"role": "user", "content": message})

if __name__ == "__main__":
    model_picker = ModelPicker(model="llama3.3")
    print(model_picker.decide_on_model())


# import openai
# import os
# import torch
# from dotenv import load_dotenv
# from model_picker import ModelPicker
# from openai import OpenAI
# from transformers import pipeline, set_seed
# from transformers import BioGptTokenizer, BioGptForCausalLM
#
# # Get API Keys
# load_dotenv(override=True)
# api_key = os.getenv('OPENAI_API_KEY')
# hf_key = os.getenv('HF_KEY')
# ollama_add = 'http://localhost:11434/v1'
# ollama_api_key = "ollama"
#
#
# biogpt = BioGptForCausalLM.from_pretrained("microsoft/biogpt")
# biogpt_tokenizer = BioGptTokenizer.from_pretrained("microsoft/biogpt")
# biogpt_generator = pipeline('text-generation', model=biogpt, tokenizer=biogpt_tokenizer)
# set_seed(42)
#
#
# llama_pipeline = pipeline("text-generation", model="meta-llama/Meta-Llama-3-8B",
#                           model_kwargs={"torch_dtype": torch.bfloat16}, token = hf_key,
#                           device_map="auto")
#
# def ask_bio_gpt(input_text):
#     response = biogpt_generator(input_text, max_length=2000, num_return_sequences=1, do_sample=True)[0][
#         "generated_text"]
#     return response
#
#
# def ask_llama(input_text):
#     response = llama_pipeline(input_text, max_length=2000, num_return_sequences=1, do_sample=True)[0]["generated_text"]
#     return response
#
#
# def conversate(user_message, messages, model="OpenAI"):
#     messages.append(
#         {"role": "user", "content": user_message}
#     )
#     if model=="OpenAI":
#         openai = OpenAI()
#         model = "gpt-4o-mini"
#     elif model=="ollama":
#         openai = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
#         model = "llama3.2"
#
#     try:
#         response = openai.chat.completions.create(model=model, messages=messages)
#     except Exception as e:
#         if "openai.NotFoundError" in str(type(e)):
#             import subprocess
#             subprocess.run(["ollama", "pull", model])
#             print(f"Pulling {model}")
#             response = openai.chat.completions.create(model=model, messages=messages)
#     return response
#
#
# model_picker = ModelPicker()
#
# system_prompt = "You are a nobel prize winning biologist."
# messages = [
#     {"role": "system", "content": system_prompt}
# ]
# response = "Blah blah blah"
# while response != "stop":
#     model_picker.decide_on_model()
#     user_prompt = input("Whaddaya want? Type 'stop' to quit.\n")
#     response = conversate(user_prompt, messages, model="ollama")
#     print(response.choices[0].message.content)
#
# #"olama serve" in powershell to get opensource llama running
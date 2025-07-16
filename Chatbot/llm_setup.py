from langchain_community.llms import Ollama

def get_ollama_llm(model_name="llama3.2:1b"):

    return Ollama(model=model_name)
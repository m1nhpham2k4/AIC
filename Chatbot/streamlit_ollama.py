from langchain_community.llms import Ollama
import getpass
import os
import streamlit as st

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

try:
    # load environment variables from .env file (requires `python-dotenv`)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

os.environ["LANGSMITH_TRACING"] = "true"
if "LANGSMITH_API_KEY" not in os.environ:
    os.environ["LANGSMITH_API_KEY"] = getpass.getpass(
        prompt="Enter your LangSmith API key (optional): "
    )
if "LANGSMITH_PROJECT" not in os.environ:
    os.environ["LANGSMITH_PROJECT"] = getpass.getpass(
        prompt='Enter your LangSmith Project Name (default = "default"): '
    )
    if not os.environ.get("LANGSMITH_PROJECT"):
        os.environ["LANGSMITH_PROJECT"] = "default"
    

prompt = ChatPromptTemplate.from_messages(
   [("system", "You are a helpful assistant. Please response to the queries"),
    ("user", "Question:{question}")]
)

st.title('Langchain Demo With Ollama')
input_text = st.text_input('Search the topic you want')

llm = Ollama(model='llama3.2:1b')
chain = prompt | llm | StrOutputParser()

if input_text:
    st.write(chain.invoke({"question":input_text}))
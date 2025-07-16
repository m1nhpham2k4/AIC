from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from llm_setup import get_ollama_llm

# 1. Load model
llm = get_ollama_llm()

# 2. Tạo Prompt (có hướng dẫn tiếng Việt)
prompt = ChatPromptTemplate.from_messages([
    ("system", "Bạn là một trợ lý AI thân thiện. Hãy trả lời bằng tiếng Việt."),
    ("human", "{message}")
])

# 3. Output parser: lấy ra chuỗi từ phản hồi
output_parser = StrOutputParser()

# 4. Chain
chain = prompt | llm | output_parser

# 5. Memory cho từng session
memory_store = {}
def get_memory(session_id):
    if session_id not in memory_store:
        memory_store[session_id] = InMemoryChatMessageHistory()
    return memory_store[session_id]

# 6. Kết hợp với memory
chat_with_memory = RunnableWithMessageHistory(
    chain,
    get_memory,
    input_messages_key="message",
    history_messages_key="messages"
)

# 7. Hàm gọi chat
def chat_with_bot(message: str, session_id: str = "default") -> str:
    return chat_with_memory.invoke(
        {"message": message},
        config={"configurable": {"session_id": session_id}}
    )

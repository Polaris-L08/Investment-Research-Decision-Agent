import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.tools.financial import get_stock_price

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0,
)

llm_with_tools = llm.bind_tools([get_stock_price])

response = llm_with_tools.invoke("What is the current stock price of AAPL?")

print("content:")
print(response.content)

print("\ntool_calls:")
print(response.tool_calls)
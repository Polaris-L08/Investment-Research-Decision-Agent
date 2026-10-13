import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()


llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0,
    extra_body={
        "thinking": {
            "type": "disabled"  # 关键：关闭思考模式
        }
    }
)
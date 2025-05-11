import os
from config import config
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from .langchain_tools import SklearnLinearRegressionTool

# 优先从config.yaml读取openai_api_key和openai_base_url
openai_api_key = getattr(config, 'OPENAI_API_KEY', None) or os.environ.get("OPENAI_API_KEY")
openai_base_url = getattr(config, 'OPENAI_BASE_URL', None) or os.environ.get("OPENAI_BASE_URL")
if not openai_api_key:
    raise RuntimeError("请在config.yaml或环境变量中设置 OPENAI_API_KEY，否则无法使用LangChain LLM Agent。")

llm_kwargs = {"temperature": 0, "openai_api_key": openai_api_key, "model": "gpt-4o"}
if openai_base_url:
    llm_kwargs["base_url"] = openai_base_url

llm = ChatOpenAI(**llm_kwargs)

tools = [
    SklearnLinearRegressionTool()
]

react_agent = initialize_agent(
    tools=tools,
    llm=llm,
    verbose=True
)

def run_agent(input_text: str):
    """
    运行智能体，输入自然语言指令，自动调用工具。
    """
    return react_agent.invoke(input_text)

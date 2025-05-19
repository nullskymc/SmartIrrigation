import os
from src.config import config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
from .langchain_tools import SklearnLinearRegressionTool

# 统一的 system prompt，描述智能体能力
SYSTEM_PROMPT = """
你是一个智能灌溉系统助手，擅长数据分析、预测和决策。你可以：
1. 分析和预测土壤湿度等环境数据
2. 调用机器学习工具（如线性回归）进行建模
3. 查询天气信息和预报数据
4. 根据用户指令自动选择合适的工具
5. 用简洁、专业的中文回答用户问题
"""

def get_agent_executor():
    # 读取 openai 配置
    openai_api_key = getattr(config, 'OPENAI_API_KEY', None) or os.environ.get("OPENAI_API_KEY")
    openai_base_url = getattr(config, 'OPENAI_BASE_URL', None) or os.environ.get("OPENAI_BASE_URL")
    if not openai_api_key:
        raise RuntimeError("请在config.yaml或环境变量中设置 OPENAI_API_KEY，否则无法使用LangChain LLM Agent。")
    llm_kwargs = {"temperature": 0, "openai_api_key": openai_api_key, "model": getattr(config, 'MODEL_NAME', 'gpt-4o')}
    if openai_base_url:
        llm_kwargs["base_url"] = openai_base_url
    llm = ChatOpenAI(**llm_kwargs)

    # 工具列表，可扩展
    # 在这里导入WeatherTool以避免循环导入
    from .weather_tools import WeatherTool
    tools = [
        SklearnLinearRegressionTool(),
        WeatherTool()  # 新增天气查询工具
    ]

    # 构建 Prompt（去掉 chat_history）
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # 构建 agent
    chat_agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=chat_agent, tools=tools)
    return agent_executor

# 统一入口
_agent_executor = None

def run_agent(input_text: str):
    """
    运行智能体，输入自然语言指令，自动调用工具。
    返回结构化 answer，兼容 SeAgent 风格。
    """
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = get_agent_executor()
    result = _agent_executor.invoke({"question": input_text})
    # 兼容 output 字段或直接返回
    if isinstance(result, dict):
        if "output" in result:
            answer = result["output"]
        elif "answer" in result:
            answer = result["answer"]
        else:
            answer = str(result)
        return {"answer": answer, **result}
    return {"answer": str(result)}

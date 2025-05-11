"""
LLM智能体模块 - 基于LangChain实现，支持ReAct Agent与sklearn工具
"""
from typing import Dict, Any, Optional
from logger_config import logger
from alarm.alarm import AlarmModule
from config import config
from .langchain_agent import run_agent

class LLMAgentModule:
    """
    基于LangChain的智能体模块，支持自然语言决策、工具调用与报警
    """
    def __init__(self, alarm_module: AlarmModule = None, irrigation_strategy: Dict[str, Any] = None):
        self.alarm_module = alarm_module
        self.irrigation_strategy = irrigation_strategy or config.IRRIGATION_STRATEGY
        self.threshold = self.irrigation_strategy.get("soil_moisture_threshold", 30.0)
        logger.info("LangChain LLM Agent initialized.")

    def run(self, user_input: str) -> str:
        """
        统一入口：用自然语言驱动LangChain Agent，可自动调用sklearn工具或自定义决策。
        """
        logger.info(f"LLM Agent收到指令: {user_input}")
        try:
            result = run_agent(user_input)
            return str(result)
        except Exception as e:
            logger.error(f"LangChain Agent执行异常: {e}")
            return f"智能体执行失败: {e}"

    def make_decision(self, current_humidity: float, predicted_humidity: Optional[float] = None) -> Dict[str, Any]:
        """
        兼容原有决策逻辑：可被外部直接调用
        """
        logger.info(f"基于当前湿度: {current_humidity}% 和预测湿度: {predicted_humidity}% 做出灌溉决策")
        decision = {"control_command": "no_action", "reason": "湿度充足，无需灌溉。"}
        trigger_irrigation = False
        reason = ""
        if current_humidity < self.threshold:
            trigger_irrigation = True
            reason = f"当前湿度 ({current_humidity}%) 低于阈值 ({self.threshold}%)。"
        elif predicted_humidity is not None and predicted_humidity < self.threshold:
            trigger_irrigation = True
            reason = f"预测未来湿度 ({predicted_humidity}%) 将低于阈值 ({self.threshold}%)。"
        if trigger_irrigation:
            decision["control_command"] = "start_irrigation"
            decision["reason"] = reason
            logger.info(f"决策: 启动灌溉。原因: {reason}")
        else:
            logger.info("决策: 无需灌溉或停止灌溉（如果正在运行）。")
        # 检查是否需要触发报警
        if self.alarm_module:
            alarm_message = self.alarm_module.handle_alarm(current_humidity)
            if alarm_message:
                decision["alarm"] = alarm_message
        return decision

    def generate_response(self, action: str, result: Any) -> str:
        """
        兼容原有响应生成逻辑
        """
        if action == "start_irrigation":
            if isinstance(result, dict) and result.get("status") == "success":
                return "已成功启动灌溉系统。"
            elif isinstance(result, dict) and result.get("status") == "warning":
                return f"注意: {result.get('message', '灌溉已在运行中')}"
            else:
                return f"启动灌溉失败: {result.get('message', '未知错误')}"
        elif action == "stop_irrigation":
            if isinstance(result, dict) and result.get("status") == "success":
                return "已成功停止灌溉系统。"
            elif isinstance(result, dict) and result.get("status") == "warning":
                return f"注意: {result.get('message', '灌溉已停止')}"
            else:
                return f"停止灌溉失败: {result.get('message', '未知错误')}"
        elif action == "predict_humidity":
            return f"预测的未来土壤湿度为: {result:.2f}%"
        elif action == "get_status":
            if isinstance(result, str):
                return f"系统状态: {result}"
            else:
                status_items = []
                for key, value in result.items():
                    status_items.append(f"{key}: {value}")
                return "系统状态:\n" + "\n".join(status_items)
        elif action == "enable_alarm" or action == "disable_alarm":
            return f"已{result}报警系统。"
        elif action == "set_threshold":
            return f"已将灌溉阈值设置为: {result}%"
        elif action == "unknown":
            return f"抱歉，我无法理解命令: '{getattr(result, 'original_command', '')}'。请使用有效的指令，如'启动灌溉'、'查看状态'等。"
        return "操作已完成。"

    def parse_command(self, command: str):
        """
        兼容UI调用，自动用langchain agent解析自然语言指令。
        返回格式：{'action': 'tool_name', ...}
        """
        try:
            result = run_agent(command)
            # 可根据实际agent返回内容做结构化处理
            return {"action": "langchain_agent", "result": result}
        except Exception as e:
            return {"action": "error", "error": str(e)}
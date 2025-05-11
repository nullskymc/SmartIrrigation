"""
LLM智能体模块 - 协调数据、模型、决策和报警
"""
from typing import Dict, Any, Optional

from src.logger_config import logger
from src.exceptions import LLMCommandError
from src.ml.ml_model import SoilMoisturePredictor
from src.alarm.alarm import AlarmModule
from src.config import config

class LLMAgentModule:
    """
    LLM智能体模块，协调数据、模型、决策和报警
    """
    def __init__(self, ml_model: SoilMoisturePredictor, alarm_module: AlarmModule, irrigation_strategy: Dict[str, Any] = None):
        """
        初始化LLM智能体
        
        :param ml_model: 机器学习模型实例
        :param alarm_module: 报警模块实例
        :param irrigation_strategy: 灌溉策略字典，默认使用配置
        """
        self.ml_model = ml_model
        self.alarm_module = alarm_module
        self.irrigation_strategy = irrigation_strategy or config.IRRIGATION_STRATEGY
        self.threshold = self.irrigation_strategy.get("soil_moisture_threshold", 30.0)
        logger.info("LLMAgentModule initialized.")
    
    def parse_command(self, command: str) -> Dict[str, Any]:
        """
        解析用户的自然语言指令
        
        :param command: 用户输入的字符串
        :return: 包含'action'和其他参数的字典
        :raises: LLMCommandError 如果无法解析命令
        """
        command_lower = command.lower()
        logger.info(f"解析命令: '{command}'")
        
        # 简化的命令解析，实际可能需要更复杂的NLP或调用外部LLM
        if "灌溉" in command_lower and ("开始" in command_lower or "启动" in command_lower):
            return {"action": "start_irrigation"}
        elif "灌溉" in command_lower and ("停止" in command_lower or "关闭" in command_lower):
            return {"action": "stop_irrigation"}
        elif "预测" in command_lower and "湿度" in command_lower:
            # 尝试提取预测时长（简化）
            hours = 24  # 默认预测24小时
            try:
                # 非常简单的提取逻辑，需要改进
                if "小时" in command_lower:
                    parts = command_lower.split("预测")[1].split("小时")[0].split()
                    for part in parts:
                        if part.isdigit():
                            hours = int(part)
                            break
            except Exception as e:
                logger.warning(f"无法从命令中解析预测小时数: {e}")
            
            return {"action": "predict_humidity", "hours": hours}
        elif "状态" in command_lower or "情况" in command_lower:
            return {"action": "get_status"}
        elif "报警" in command_lower and ("开启" in command_lower or "启用" in command_lower):
            return {"action": "enable_alarm"}
        elif "报警" in command_lower and ("关闭" in command_lower or "禁用" in command_lower):
            return {"action": "disable_alarm"}
        elif "阈值" in command_lower and "设置" in command_lower:
            # 尝试提取阈值数值
            threshold = None
            try:
                for part in command_lower.split():
                    if part.replace(".", "").isdigit():
                        threshold = float(part)
                        break
            except Exception as e:
                logger.warning(f"无法从命令中解析阈值: {e}")
            
            if threshold is not None:
                return {"action": "set_threshold", "value": threshold}
        
        # 未能识别的命令
        logger.warning(f"未知命令: '{command}'")
        return {"action": "unknown", "original_command": command}
    
    def predict_humidity(self, combined_data: Dict[str, Any]) -> float:
        """
        调用机器学习模型预测未来湿度
        
        :param combined_data: 包含当前传感器和天气数据的字典
        :return: 预测的土壤湿度值
        """
        logger.info("请求ML模型预测湿度")
        
        # 准备模型输入
        model_input = {}
        
        # 从传感器数据提取
        if "sensor_data" in combined_data:
            sensor_data = combined_data.get("sensor_data", {})
            if "data" in sensor_data:
                model_input.update(sensor_data["data"])
            elif isinstance(sensor_data, dict):
                model_input.update(sensor_data)
        
        # 从天气数据提取
        if "weather_data" in combined_data:
            weather_data = combined_data.get("weather_data", {})
            model_input["weather_temperature"] = weather_data.get("temperature")
            model_input["weather_humidity"] = weather_data.get("humidity")
        
        # 调用模型进行预测
        predicted_humidity = self.ml_model.predict(model_input)
        return predicted_humidity
    
    def make_decision(self, current_humidity: float, predicted_humidity: float = None) -> Dict[str, Any]:
        """
        根据当前湿度和预测湿度（可选）生成灌溉决策
        
        :param current_humidity: 当前土壤湿度
        :param predicted_humidity: 预测的未来土壤湿度 (可选)
        :return: 包含'control_command'和'reason'的字典
        """
        logger.info(f"基于当前湿度: {current_humidity}% 和预测湿度: {predicted_humidity}% 做出灌溉决策")
        decision = {"control_command": "no_action", "reason": "湿度充足，无需灌溉。"}
        
        trigger_irrigation = False
        reason = ""
        
        if current_humidity < self.threshold:
            trigger_irrigation = True
            reason = f"当前湿度 ({current_humidity}%) 低于阈值 ({self.threshold}%)。"
        elif predicted_humidity is not None and predicted_humidity < self.threshold:
            # 基于预测启动灌溉
            trigger_irrigation = True
            reason = f"预测未来湿度 ({predicted_humidity}%) 将低于阈值 ({self.threshold}%)。"
        
        if trigger_irrigation:
            decision["control_command"] = "start_irrigation"
            decision["reason"] = reason
            # 可以加入避免在降雨时灌溉的逻辑
            # if rainfall > threshold: decision = "no_action"
            logger.info(f"决策: 启动灌溉。原因: {reason}")
        else:
            logger.info("决策: 无需灌溉或停止灌溉（如果正在运行）。")
        
        # 检查是否需要触发报警
        alarm_message = self.alarm_module.handle_alarm(current_humidity)
        if alarm_message:
            decision["alarm"] = alarm_message  # 将报警信息附加到决策结果
        
        return decision
    
    def generate_response(self, action: str, result: Dict[str, Any]) -> str:
        """
        根据操作类型和结果生成用户友好的响应
        
        :param action: 操作类型
        :param result: 操作结果
        :return: 格式化的响应字符串
        """
        if action == "start_irrigation":
            if result.get("status") == "success":
                return "已成功启动灌溉系统。"
            elif result.get("status") == "warning":
                return f"注意: {result.get('message', '灌溉已在运行中')}"
            else:
                return f"启动灌溉失败: {result.get('message', '未知错误')}"
                
        elif action == "stop_irrigation":
            if result.get("status") == "success":
                return "已成功停止灌溉系统。"
            elif result.get("status") == "warning":
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
            return f"抱歉，我无法理解命令: '{result.get('original_command', '')}'。请使用有效的指令，如'启动灌溉'、'查看状态'等。"
            
        return "操作已完成。"
"""
用户界面模块 - 基于Gradio构建交互式用户界面
"""
import gradio as gr
from typing import Dict, Any

from src.smart_irrigation.logger_config import logger
from src.smart_irrigation.llm_agent import LLMAgentModule
from src.smart_irrigation.control_execution import ControlExecutionModule
from src.smart_irrigation.data_processing import DataProcessingModule
from src.smart_irrigation.data_collection import DataCollectionModule

class UserInterfaceModule:
    """
    基于Gradio的用户界面
    """
    def __init__(self,
                 llm_agent: LLMAgentModule,
                 control_module: ControlExecutionModule,
                 data_collector: DataCollectionModule,
                 data_processor: DataProcessingModule):
        """
        初始化用户界面模块
        
        :param llm_agent: LLM智能体实例
        :param control_module: 控制模块实例 (获取状态)
        :param data_collector: 数据采集模块实例 (获取实时数据)
        :param data_processor: 数据处理模块实例 (获取天气数据)
        """
        self.llm_agent = llm_agent
        self.control_module = control_module
        self.data_collector = data_collector
        self.data_processor = data_processor
        logger.info("UserInterfaceModule initialized.")
    
    def handle_user_input(self, user_input: str) -> str:
        """
        处理来自Gradio界面的用户输入
        
        :param user_input: 用户输入的文本命令
        :return: 系统响应字符串
        """
        logger.info(f"收到用户输入: '{user_input}'")
        
        try:
            # 解析用户命令
            parsed_command = self.llm_agent.parse_command(user_input)
            action = parsed_command.get("action")
            
            if action == "start_irrigation":
                # 获取当前数据以辅助决策
                sensor_data = self.data_collector.get_data()
                combined_data = {
                    "sensor_data": sensor_data,
                    "weather_data": {}
                }
                
                try:
                    # 获取天气数据（如果可能）
                    location = "Beijing"  # 默认位置
                    weather_result = self.data_processor.process_and_get_weather(sensor_data, location)
                    combined_data = weather_result
                except Exception as e:
                    logger.warning(f"获取天气数据失败: {e}")
                
                # 获取当前土壤湿度
                current_humidity = sensor_data["data"]["soil_moisture"]
                
                # 根据预测做决策
                try:
                    predicted_humidity = self.llm_agent.predict_humidity(combined_data)
                    decision = self.llm_agent.make_decision(current_humidity, predicted_humidity)
                except Exception as e:
                    logger.warning(f"预测湿度失败: {e}")
                    decision = self.llm_agent.make_decision(current_humidity)
                
                if decision.get('alarm'):
                    alarm_message = f"\n\n⚠️ 警报: {decision.get('alarm')}"
                else:
                    alarm_message = ""
                
                # 如果决策是启动灌溉
                if decision.get('control_command') == 'start_irrigation':
                    result = self.control_module.start_irrigation()
                    return f"根据当前湿度 {current_humidity:.1f}% 的分析，系统决定启动灌溉。\n\n{result.get('message', '灌溉已启动')}{alarm_message}"
                else:
                    reason = decision.get('reason', '湿度充足')
                    return f"根据当前湿度 {current_humidity:.1f}% 的分析，系统决定不启动灌溉。\n\n原因: {reason}{alarm_message}"
            
            elif action == "stop_irrigation":
                result = self.control_module.stop_irrigation()
                return self.llm_agent.generate_response(action, result)
            
            elif action == "predict_humidity":
                hours = parsed_command.get("hours", 24)
                # 获取当前数据和天气数据
                sensor_data = self.data_collector.get_data()
                try:
                    location = "Beijing"  # 可以从配置或用户输入获取
                    combined_data = self.data_processor.process_and_get_weather(sensor_data, location)
                    predicted = self.llm_agent.predict_humidity(combined_data)
                    return f"预测{hours}小时后的土壤湿度: {predicted:.1f}%"
                except Exception as e:
                    logger.error(f"预测湿度时发生错误: {e}", exc_info=True)
                    return f"无法预测未来湿度: {str(e)}"
            
            elif action == "get_status":
                try:
                    # 获取设备状态
                    status = self.control_module.get_status()
                    status_text = ""
                    
                    if status["device_status"] == "running":
                        status_text = f"灌溉系统: 运行中 (已运行{status.get('elapsed_minutes', 0):.1f}分钟，剩余{status.get('remaining_minutes', 0):.1f}分钟)"
                    else:
                        status_text = f"灌溉系统: {status['device_status']}"
                    
                    # 获取最新的传感器数据
                    sensor_data = self.data_collector.get_data().get('data', {})
                    humidity = sensor_data.get('soil_moisture', 'N/A')
                    temp = sensor_data.get('temperature', 'N/A')
                    light = sensor_data.get('light_intensity', 'N/A')
                    rainfall = sensor_data.get('rainfall', 'N/A')
                    
                    # 获取最新的天气数据
                    try:
                        weather = self.data_processor.get_weather_data("Beijing")
                        weather_temp = weather.get('temperature', 'N/A')
                        weather_humidity = weather.get('humidity', 'N/A')
                        weather_condition = weather.get('condition', 'N/A')
                    except:
                        weather_temp = "N/A"
                        weather_humidity = "N/A"
                        weather_condition = "N/A"
                    
                    # 组装状态信息
                    return (f"系统状态:\n"
                            f"- {status_text}\n"
                            f"- 当前土壤湿度: {humidity}%\n"
                            f"- 环境温度: {temp}°C\n"
                            f"- 光照强度: {light} lux\n"
                            f"- 降雨量: {rainfall} mm\n"
                            f"- 天气状况: {weather_condition} ({weather_temp}°C, 湿度{weather_humidity}%)")
                except Exception as e:
                    logger.error(f"获取系统状态时发生错误: {e}", exc_info=True)
                    return f"获取系统状态失败: {str(e)}"
            
            elif action == "enable_alarm":
                self.llm_agent.alarm_module.enable_alarm()
                return "已启用报警系统。"
            
            elif action == "disable_alarm":
                self.llm_agent.alarm_module.disable_alarm()
                return "已禁用报警系统。"
            
            elif action == "set_threshold":
                threshold = parsed_command.get("value")
                if threshold is not None:
                    self.llm_agent.alarm_module.set_threshold(threshold)
                    # 同时更新灌溉决策阈值
                    self.llm_agent.threshold = threshold
                    return f"已将湿度阈值设置为: {threshold}%"
                else:
                    return "错误: 未指定阈值数值。"
            
            elif action == "unknown":
                return f"抱歉，我无法理解命令: '{parsed_command.get('original_command', '')}'。\n\n请使用有效的指令，如'启动灌溉'、'停止灌溉'、'查看状态'、'预测湿度'等。"
            
            else:
                return f"命令 '{action}' 已识别但尚未实现。"
                
        except Exception as e:
            logger.error(f"处理用户输入时发生错误: {e}", exc_info=True)
            return f"处理命令时出错: {str(e)}"
    
    def create_ui(self):
        """
        创建并返回Gradio界面
        
        :return: Gradio界面对象
        """
        logger.info("正在创建Gradio界面...")
        
        # 创建界面
        with gr.Blocks(title="智能灌溉系统") as interface:
            gr.Markdown("# 智能灌溉系统控制面板")
            
            with gr.Row():
                with gr.Column(scale=2):
                    inp = gr.Textbox(
                        label="输入指令", 
                        placeholder="例如: 启动灌溉, 预测未来6小时湿度, 系统状态",
                        lines=2
                    )
                    btn = gr.Button("发送")
                
                with gr.Column(scale=3):
                    out = gr.Textbox(label="系统响应", lines=8)
            
            # 添加几个快捷按钮
            with gr.Row():
                status_btn = gr.Button("查看系统状态")
                start_btn = gr.Button("启动灌溉")
                stop_btn = gr.Button("停止灌溉")
                predict_btn = gr.Button("预测未来湿度")
            
            # 绑定事件
            btn.click(fn=self.handle_user_input, inputs=inp, outputs=out)
            status_btn.click(fn=lambda: self.handle_user_input("系统状态"), inputs=None, outputs=out)
            start_btn.click(fn=lambda: self.handle_user_input("启动灌溉"), inputs=None, outputs=out)
            stop_btn.click(fn=lambda: self.handle_user_input("停止灌溉"), inputs=None, outputs=out)
            predict_btn.click(fn=lambda: self.handle_user_input("预测未来24小时湿度"), inputs=None, outputs=out)
            
            # 可以添加更多高级功能，如数据可视化等
        
        logger.info("Gradio界面创建完成。")
        return interface
    
    def launch(self, share=False):
        """
        创建并启动Gradio界面
        
        :param share: 是否创建可分享的公共链接
        :return: None
        """
        ui = self.create_ui()
        logger.info(f"正在启动Gradio界面，share={share}")
        ui.launch(share=share)
        logger.info("Gradio界面已关闭。")
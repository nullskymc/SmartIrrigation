"""
用户界面模块 - 基于Gradio构建交互式用户界面
提供用户友好的灌溉系统控制面板和数据可视化功能
"""
import gradio as gr
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from typing import Dict, Any, List, Tuple, Optional
from matplotlib.figure import Figure

from src.logger_config import logger
from llm.llm_agent import LLMAgentModule
from control.control_execution import ControlExecutionModule
from data.data_processing import DataProcessingModule
from data.data_collection import DataCollectionModule

class UserInterfaceModule:
    """
    基于Gradio的用户界面，提供灌溉系统控制和数据可视化功能
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
        
        # 用于存储历史数据的缓存
        self.data_history = {
            "timestamp": [],
            "soil_moisture": [],
            "temperature": [],
            "light_intensity": [],
            "rainfall": []
        }
        
        # UI主题配置
        self.theme = gr.themes.Soft(
            primary_hue="teal",
            secondary_hue="blue",
        ).set(
            body_background_fill="#f7f9fc",
            block_background_fill="#ffffff",
            button_primary_background_fill="*primary_500",
            button_primary_background_fill_hover="*primary_600"
        )
        
        # 定义系统状态指示器文本和颜色
        self.system_status = {"text": "未运行", "color": "gray"}
        
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
            logger.info(f"解析到 action: {action}")
            
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
            
            elif action == "langchain_agent":
                # 优先展示 answer 字段
                answer = parsed_command.get("answer")
                if answer:
                    logger.info(f"langchain_agent answer: {answer}")
                    return str(answer)
                # 兜底展示 result
                result = parsed_command.get("result")
                if isinstance(result, dict) and "answer" in result:
                    logger.info(f"langchain_agent result.answer: {result['answer']}")
                    return str(result["answer"])
                logger.info(f"langchain_agent result: {result}")
                return str(result)
            
            elif action == "unknown":
                logger.info("action unknown，fallback 到 langchain_agent.run")
                # fallback 到 langchain_agent.run
                agent_result = self.llm_agent.run(user_input)
                logger.info(f"langchain_agent.run 返回: {agent_result}")
                return str(agent_result)
            
            else:
                logger.info(f"action '{action}' 未实现，fallback 到 langchain_agent.run")
                agent_result = self.llm_agent.run(user_input)
                logger.info(f"langchain_agent.run 返回: {agent_result}")
                return str(agent_result)
                
        except Exception as e:
            logger.error(f"处理用户输入时发生错误: {e}", exc_info=True)
            return f"处理命令时出错: {str(e)}"
    
    def create_ui(self):
        """
        创建并返回Gradio界面
        
        :return: Gradio界面对象
        """
        logger.info("正在创建Gradio界面...")
        
        # 生成初始状态和数据
        self.update_data_history()  # 获取初始数据
        status_text, status_color = self.get_system_status_display()
        readings = self.get_current_readings()
        
        # 创建界面
        with gr.Blocks(title="智能灌溉系统", theme=self.theme, css="#title-banner {background-color: #1abc9c;}") as interface:
            with gr.Row(elem_id="title-banner"):
                gr.Markdown("# 🌱 智能灌溉系统控制面板")
            
            # 顶部状态栏
            with gr.Row():
                with gr.Column(scale=1):
                    status_indicator = gr.HTML(
                        f'<div style="display:flex;align-items:center;"><div style="width:15px;height:15px;border-radius:50%;background-color:{status_color};margin-right:10px"></div>系统状态: {status_text}</div>'
                    )
                
                with gr.Column(scale=1):
                    current_time = gr.Markdown(datetime.datetime.now().strftime("当前时间: %Y-%m-%d %H:%M:%S"))
                
                with gr.Column(scale=1):
                    refresh_btn = gr.Button("🔄 刷新数据", variant="secondary")
            
            # 主控制界面与数据
            with gr.Tabs() as tabs:
                # 控制面板选项卡
                with gr.TabItem("控制面板"):
                    with gr.Row():
                        # 左侧控制区
                        with gr.Column(scale=2):
                            # 命令输入区域
                            with gr.Group():
                                gr.Markdown("### 🎮 系统控制")
                                inp = gr.Textbox(
                                    label="输入指令", 
                                    placeholder="例如: 启动灌溉, 预测未来6小时湿度, 系统状态",
                                    lines=2
                                )
                                btn = gr.Button("发送", variant="primary")
                                
                                # 常用操作快捷按钮
                                with gr.Row():
                                    start_btn = gr.Button("🟢 启动灌溉", variant="primary")
                                    stop_btn = gr.Button("🔴 停止灌溉")
                                    status_btn = gr.Button("📊 系统状态", variant="secondary")
                                    predict_btn = gr.Button("🔮 预测湿度", variant="secondary")
                            
                            # 阈值设置区域
                            with gr.Group():
                                gr.Markdown("### ⚙️ 灌溉设置")
                                with gr.Row():
                                    threshold_slider = gr.Slider(
                                        minimum=10, maximum=90, value=30, step=1,
                                        label="湿度阈值 (%)", info="土壤湿度低于此值时会触发自动灌溉"
                                    )
                                    set_threshold_btn = gr.Button("设置阈值")
                                    
                                with gr.Row():
                                    with gr.Column(scale=1, min_width=100):
                                        alarm_enable = gr.Checkbox(label="启用报警", value=True)
                                    with gr.Column(scale=2):
                                        alarm_update_btn = gr.Button("更新报警设置")
                        
                        # 右侧信息显示区
                        with gr.Column(scale=3):
                            # 系统响应区域
                            out = gr.Textbox(label="系统响应", lines=8)
                            
                            # 当前传感器数据显示
                            with gr.Group():
                                gr.Markdown("### 📈 当前读数")
                                with gr.Row():
                                    with gr.Column(scale=1):
                                        soil_moisture = gr.Markdown(f"**土壤湿度:** {readings['soil_moisture']}%")
                                        temperature = gr.Markdown(f"**环境温度:** {readings['temperature']}°C")
                                    with gr.Column(scale=1):
                                        light = gr.Markdown(f"**光照强度:** {readings['light_intensity']} lux")
                                        rainfall = gr.Markdown(f"**降雨量:** {readings['rainfall']} mm")
                                
                                # 天气数据
                                gr.Markdown("### ☁️ 天气信息")
                                with gr.Row():
                                    with gr.Column(scale=1):
                                        w_condition = gr.Markdown(f"**天气状况:** {readings['weather_condition']}")
                                        w_temp = gr.Markdown(f"**气温:** {readings['weather_temp']}°C")
                                    with gr.Column(scale=1):
                                        w_humidity = gr.Markdown(f"**空气湿度:** {readings['weather_humidity']}%")
                                        w_precip = gr.Markdown(f"**降水概率:** {readings['weather_precipitation']}%")
                
                # 数据可视化选项卡
                with gr.TabItem("数据可视化"):
                    with gr.Row():
                        # 图表选择器
                        chart_type = gr.Radio(
                            ["土壤湿度趋势", "多传感器数据", "灌溉历史", "天气预报"],
                            label="选择图表类型",
                            value="土壤湿度趋势"
                        )
                        update_chart_btn = gr.Button("更新图表", variant="primary")
                    
                    # 图表显示区域
                    with gr.Group():
                        chart_output = gr.Plot(self.generate_soil_moisture_chart())
                    
                    # 图表说明
                    with gr.Accordion("图表说明", open=False):
                        gr.Markdown("""
                        - **土壤湿度趋势**: 显示土壤湿度的历史变化趋势
                        - **多传感器数据**: 对比显示土壤湿度、温度和光照强度的变化
                        - **灌溉历史**: 显示系统灌溉活动的历史记录
                        - **天气预报**: 显示未来天气预报数据
                        """)
                
                # 系统日志选项卡
                with gr.TabItem("系统日志"):
                    with gr.Row():
                        log_level = gr.Dropdown(
                            ["全部", "信息", "警告", "错误"],
                            label="日志级别",
                            value="全部"
                        )
                        refresh_logs_btn = gr.Button("刷新日志", variant="primary")
                    
                    # 模拟日志数据
                    example_logs = [
                        [datetime.datetime.now().strftime("%H:%M:%S"), "INFO", "系统已启动"],
                        [(datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime("%H:%M:%S"), "INFO", "获取传感器数据成功"],
                        [(datetime.datetime.now() - datetime.timedelta(minutes=10)).strftime("%H:%M:%S"), "WARNING", "土壤湿度低于阈值"],
                        [(datetime.datetime.now() - datetime.timedelta(minutes=15)).strftime("%H:%M:%S"), "INFO", "启动灌溉"],
                        [(datetime.datetime.now() - datetime.timedelta(minutes=20)).strftime("%H:%M:%S"), "INFO", "获取天气数据"],
                        [(datetime.datetime.now() - datetime.timedelta(minutes=25)).strftime("%H:%M:%S"), "ERROR", "天气API连接超时"]
                    ]
                    
                    # 日志显示区域 - 使用初始值而非后续更新
                    log_output = gr.Dataframe(
                        value=example_logs,
                        headers=["时间", "级别", "消息"],
                        datatype=["str", "str", "str"],
                        row_count=(10, "fixed"),
                        col_count=(3, "fixed")
                    )
                
                # 帮助选项卡
                with gr.TabItem("帮助"):
                    gr.Markdown("""
                    ## 智能灌溉系统使用指南
                    
                    ### 🎮 基本控制命令:
                    - **启动灌溉**: 手动开启灌溉系统
                    - **停止灌溉**: 手动停止灌溉系统
                    - **系统状态**: 查询当前系统状态和传感器数据
                    - **预测湿度**: 预测未来土壤湿度变化
                    
                    ### 🔧 高级命令示例:
                    - **预测未来6小时湿度**: 指定时间范围进行预测
                    - **设置湿度阈值为40**: 更改灌溉自动触发阈值
                    - **启用/禁用报警**: 控制报警系统
                    
                    ### 📱 数据可视化:
                    切换到"数据可视化"选项卡查看各种数据图表，包括土壤湿度趋势、多传感器数据对比等。
                    
                    ### 📋 系统日志:
                    在"系统日志"选项卡查看系统运行记录，可按日志级别筛选。
                    
                    ### 🧠 智能决策:
                    系统将基于当前土壤湿度、历史数据和天气预报，智能决定是否需要灌溉。
                    """)
            
            # 页脚
            with gr.Row():
                gr.Markdown("© 2025 智能灌溉系统 | 版本 1.0")
            
            # 绑定事件
            btn.click(fn=self.handle_user_input, inputs=inp, outputs=out)
            status_btn.click(fn=lambda: self.handle_user_input("系统状态"), inputs=None, outputs=out)
            start_btn.click(fn=lambda: self.handle_user_input("启动灌溉"), inputs=None, outputs=out)
            stop_btn.click(fn=lambda: self.handle_user_input("停止灌溉"), inputs=None, outputs=out)
            predict_btn.click(fn=lambda: self.handle_user_input("预测未来24小时湿度"), inputs=None, outputs=out)
            
            # 设置阈值按钮事件
            def handle_set_threshold(value):
                result = self.handle_user_input(f"设置湿度阈值为{value}")
                return result
            
            set_threshold_btn.click(fn=handle_set_threshold, inputs=threshold_slider, outputs=out)
            
            # 更新报警设置事件
            def handle_alarm_update(enabled):
                if enabled:
                    result = self.handle_user_input("启用报警")
                else:
                    result = self.handle_user_input("禁用报警")
                return result
            
            alarm_update_btn.click(fn=handle_alarm_update, inputs=alarm_enable, outputs=out)
            
            # 刷新数据事件
            def refresh_data():
                self.update_data_history()
                status_text, status_color = self.get_system_status_display()
                readings = self.get_current_readings()
                
                # 更新状态指示器
                status_html = f'<div style="display:flex;align-items:center;"><div style="width:15px;height:15px;border-radius:50%;background-color:{status_color};margin-right:10px"></div>系统状态: {status_text}</div>'
                
                # 更新时间
                current_time_str = datetime.datetime.now().strftime("当前时间: %Y-%m-%d %H:%M:%S")
                
                # 更新传感器读数
                soil_str = f"**土壤湿度:** {readings['soil_moisture']}%"
                temp_str = f"**环境温度:** {readings['temperature']}°C"
                light_str = f"**光照强度:** {readings['light_intensity']} lux"
                rainfall_str = f"**降雨量:** {readings['rainfall']} mm"
                
                # 更新天气信息
                w_cond_str = f"**天气状况:** {readings['weather_condition']}"
                w_temp_str = f"**气温:** {readings['weather_temp']}°C"
                w_hum_str = f"**空气湿度:** {readings['weather_humidity']}%"
                w_prec_str = f"**降水概率:** {readings['weather_precipitation']}%"
                
                return (
                    status_html, current_time_str,
                    soil_str, temp_str, light_str, rainfall_str,
                    w_cond_str, w_temp_str, w_hum_str, w_prec_str
                )
            
            refresh_btn.click(
                fn=refresh_data,
                inputs=None,
                outputs=[
                    status_indicator, current_time,
                    soil_moisture, temperature, light, rainfall,
                    w_condition, w_temp, w_humidity, w_precip
                ]
            )
            
            # 更新图表事件
            def update_chart(chart_type):
                # 设置Matplotlib支持中文显示
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
                plt.rcParams['axes.unicode_minus'] = False
                
                if chart_type == "土壤湿度趋势":
                    return self.generate_soil_moisture_chart()
                elif chart_type == "多传感器数据":
                    return self.generate_multi_sensor_chart()
                else:
                    # 其他图表类型（可以根据需要实现）
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.text(0.5, 0.5, f"Feature under development...", 
                           horizontalalignment='center', verticalalignment='center',
                           transform=ax.transAxes, fontsize=14)
                    return fig
            
            update_chart_btn.click(fn=update_chart, inputs=chart_type, outputs=chart_output)
            chart_type.change(fn=update_chart, inputs=chart_type, outputs=chart_output)
            
            # 刷新日志事件
            def refresh_logs(level):
                # 模拟从日志文件获取数据
                # 实际实现应该从系统日志文件读取
                now = datetime.datetime.now()
                
                # 生成新的日志数据（模拟新的时间戳）
                updated_logs = [
                    [now.strftime("%H:%M:%S"), "INFO", "系统已启动"],
                    [(now - datetime.timedelta(minutes=5)).strftime("%H:%M:%S"), "INFO", "获取传感器数据成功"],
                    [(now - datetime.timedelta(minutes=10)).strftime("%H:%M:%S"), "WARNING", "土壤湿度低于阈值"],
                    [(now - datetime.timedelta(minutes=15)).strftime("%H:%M:%S"), "INFO", "启动灌溉"],
                    [(now - datetime.timedelta(minutes=20)).strftime("%H:%M:%S"), "INFO", "获取天气数据"],
                    [(now - datetime.timedelta(minutes=25)).strftime("%H:%M:%S"), "ERROR", "天气API连接超时"]
                ]
                
                # 根据选择的级别过滤日志
                if level == "全部":
                    return updated_logs
                elif level == "信息":
                    return [log for log in updated_logs if log[1] == "INFO"]
                elif level == "警告":
                    return [log for log in updated_logs if log[1] == "WARNING"]
                elif level == "错误":
                    return [log for log in updated_logs if log[1] == "ERROR"]
                else:
                    return updated_logs
            
            # 在gradio中，直接返回新的dataframe值来替换旧值
            refresh_logs_btn.click(fn=refresh_logs, inputs=log_level, outputs=log_output)
            log_level.change(fn=refresh_logs, inputs=log_level, outputs=log_output)
        
        logger.info("Gradio界面创建完成。")
        return interface
    
    def launch(self, share=False, server_port=7860, server_name="0.0.0.0", auth=None, ssl_verify=True):
        """
        创建并启动Gradio界面
        
        :param share: 是否创建可分享的公共链接
        :param server_port: 服务器端口
        :param server_name: 服务器名称/IP地址
        :param auth: 认证信息 (None 或 (username, password) 元组)
        :param ssl_verify: 是否验证SSL证书
        :return: None
        """
        ui = self.create_ui()
        logger.info(f"正在启动Gradio界面，share={share}，port={server_port}")
        
        # 定义定时回调函数，每隔一段时间更新数据历史
        def periodic_update():
            self.update_data_history()
            logger.debug("定期数据更新已执行")
        
        # 启动UI，并设置定期数据更新
        ui.launch(
            share=share,
            server_port=server_port,
            server_name=server_name,
            auth=auth,
            ssl_verify=ssl_verify,
            prevent_thread_lock=True  # 允许在主线程之外运行
        )
        
        # 注意：如果需要定期更新，应该在实际实现中考虑使用单独的线程
        # 以下代码仅做示例，实际应用中应考虑线程安全
        try:
            while True:
                time.sleep(60)  # 每分钟更新一次
                periodic_update()
        except KeyboardInterrupt:
            logger.info("检测到键盘中断，停止更新线程")
        finally:
            logger.info("Gradio界面已关闭。")
    
    def generate_soil_moisture_chart(self) -> Figure:
        """
        生成土壤湿度历史数据图表
        
        :return: matplotlib图表对象
        """
        try:
            # 设置Matplotlib支持中文显示
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
            plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
            
            # 如果没有足够的数据，生成一些模拟数据用于显示
            if len(self.data_history["timestamp"]) < 2:
                # 生成一些模拟数据用于初始显示
                now = datetime.datetime.now()
                timestamps = [(now - datetime.timedelta(hours=i)).strftime('%H:%M') for i in range(24, 0, -1)]
                # 模拟一些波动的湿度数据
                base_moisture = 50 + np.random.normal(0, 5, 24)
                # 确保湿度在合理范围内
                moistures = np.clip(base_moisture, 0, 100)
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(timestamps, moistures, marker='o', linestyle='-', color='#2980b9')
                ax.set_title('Soil Moisture History (Simulated)', fontsize=14)  # 使用英文避免字体问题
                ax.set_xlabel('Time', fontsize=12)  # 使用英文避免字体问题
                ax.set_ylabel('Moisture (%)', fontsize=12)  # 使用英文避免字体问题
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.set_ylim(0, 100)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                return fig
            else:
                # 使用实际收集的历史数据
                timestamps = self.data_history["timestamp"][-24:]  # 最近24个数据点
                moistures = self.data_history["soil_moisture"][-24:]
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(timestamps, moistures, marker='o', linestyle='-', color='#2980b9')
                ax.set_title('Soil Moisture History', fontsize=14)  # 使用英文避免字体问题
                ax.set_xlabel('Time', fontsize=12)  # 使用英文避免字体问题
                ax.set_ylabel('Moisture (%)', fontsize=12)  # 使用英文避免字体问题
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.set_ylim(0, 100)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                return fig
        except Exception as e:
            logger.error(f"生成土壤湿度图表出错: {e}", exc_info=True)
            # 出错时返回一个空白图表
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"生成图表出错: {str(e)}", horizontalalignment='center', 
                    verticalalignment='center', transform=ax.transAxes)
            return fig
    
    def generate_multi_sensor_chart(self) -> Figure:
        """
        生成多传感器数据对比图表
        
        :return: matplotlib图表对象
        """
        try:
            # 设置Matplotlib支持中文显示
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
            plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
            
            # 如果没有足够的数据，生成一些模拟数据用于显示
            if len(self.data_history["timestamp"]) < 2:
                # 生成模拟数据
                now = datetime.datetime.now()
                timestamps = [(now - datetime.timedelta(hours=i)).strftime('%H:%M') for i in range(12, 0, -1)]
                
                # 模拟几种不同的传感器数据
                moisture_data = np.clip(50 + np.random.normal(0, 8, 12), 0, 100)  # 湿度数据
                temp_data = 20 + np.random.normal(0, 3, 12)  # 温度数据
                light_data = np.clip(5000 + np.random.normal(0, 1000, 12), 0, 10000)  # 光照数据
                light_data_scaled = light_data / 100  # 缩放光照数据以便在同一图表显示
                
                fig, ax1 = plt.subplots(figsize=(10, 6))
                
                # 湿度数据 (主Y轴)
                ax1.set_xlabel('Time', fontsize=12)  # 使用英文避免字体问题
                ax1.set_ylabel('Moisture (%) / Temperature (°C)', fontsize=12)  # 使用英文避免字体问题
                line1 = ax1.plot(timestamps, moisture_data, color='#3498db', marker='o', label='Soil Moisture (%)')
                line2 = ax1.plot(timestamps, temp_data, color='#e74c3c', marker='^', label='Temperature (°C)')
                ax1.set_ylim(0, 100)
                
                # 光照数据 (次Y轴)
                ax2 = ax1.twinx()
                ax2.set_ylabel('Light Intensity (x100 lux)', fontsize=12)  # 使用英文避免字体问题
                line3 = ax2.plot(timestamps, light_data_scaled, color='#f39c12', marker='s', label='Light Intensity (x100 lux)')
                ax2.set_ylim(0, 100)
                
                # 合并图例
                lines = line1 + line2 + line3
                labels = [l.get_label() for l in lines]
                ax1.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
                
                ax1.set_title('Multi-Sensor Data Comparison (Simulated)', fontsize=14)  # 使用英文避免字体问题
                ax1.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                return fig
            else:
                # 使用实际收集的历史数据
                timestamps = self.data_history["timestamp"][-12:]  # 最近12个数据点
                moistures = self.data_history["soil_moisture"][-12:]
                temps = self.data_history["temperature"][-12:]
                lights = self.data_history["light_intensity"][-12:]
                lights_scaled = [l/100 for l in lights]  # 缩放光照数据以便在同一图表显示
                
                fig, ax1 = plt.subplots(figsize=(10, 6))
                
                # 湿度数据 (主Y轴)
                ax1.set_xlabel('Time', fontsize=12)  # 使用英文避免字体问题
                ax1.set_ylabel('Moisture (%) / Temperature (°C)', fontsize=12)  # 使用英文避免字体问题
                line1 = ax1.plot(timestamps, moistures, color='#3498db', marker='o', label='Soil Moisture (%)')
                line2 = ax1.plot(timestamps, temps, color='#e74c3c', marker='^', label='Temperature (°C)')
                ax1.set_ylim(0, 100)
                
                # 光照数据 (次Y轴)
                ax2 = ax1.twinx()
                ax2.set_ylabel('Light Intensity (x100 lux)', fontsize=12)  # 使用英文避免字体问题
                line3 = ax2.plot(timestamps, lights_scaled, color='#f39c12', marker='s', label='Light Intensity (x100 lux)')
                ax2.set_ylim(0, 100)
                
                # 合并图例
                lines = line1 + line2 + line3
                labels = [l.get_label() for l in lines]
                ax1.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
                
                ax1.set_title('Multi-Sensor Data Comparison', fontsize=14)  # 使用英文避免字体问题
                ax1.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                return fig
        except Exception as e:
            logger.error(f"生成多传感器图表出错: {e}", exc_info=True)
            # 出错时返回一个空白图表
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"生成图表出错: {str(e)}", horizontalalignment='center', 
                    verticalalignment='center', transform=ax.transAxes)
            return fig
    
    def update_data_history(self):
        """
        更新历史数据缓存
        """
        try:
            # 获取最新传感器数据
            sensor_data = self.data_collector.get_data().get('data', {})
            
            # 添加时间戳
            self.data_history["timestamp"].append(datetime.datetime.now().strftime('%H:%M'))
            
            # 添加传感器数据
            self.data_history["soil_moisture"].append(sensor_data.get('soil_moisture', 0))
            self.data_history["temperature"].append(sensor_data.get('temperature', 0))
            self.data_history["light_intensity"].append(sensor_data.get('light_intensity', 0))
            self.data_history["rainfall"].append(sensor_data.get('rainfall', 0))
            
            # 保持历史数据在合理的大小范围内（保留最近100条数据）
            max_history = 100
            for key in self.data_history:
                if len(self.data_history[key]) > max_history:
                    self.data_history[key] = self.data_history[key][-max_history:]
            
            logger.info("历史数据已更新")
            return True
        except Exception as e:
            logger.error(f"更新历史数据时出错: {e}", exc_info=True)
            return False
    
    def get_system_status_display(self) -> Tuple[str, str]:
        """
        获取用于显示的系统状态信息和颜色
        
        :return: 状态文本和HTML颜色代码元组
        """
        try:
            status = self.control_module.get_status()
            
            if status["device_status"] == "running":
                return f"运行中 ({status.get('elapsed_minutes', 0):.1f}分钟)", "#27ae60"
            elif status["device_status"] == "idle":
                return "空闲", "#3498db"
            elif status["device_status"] == "error":
                return "错误", "#e74c3c"
            elif status["device_status"] == "disabled":
                return "已禁用", "#95a5a6"
            else:
                return status["device_status"], "#f39c12"
        except Exception as e:
            logger.error(f"获取系统状态显示时出错: {e}", exc_info=True)
            return "未知", "#e74c3c"
            
    def get_current_readings(self) -> Dict[str, Any]:
        """
        获取当前传感器读数和天气数据
        
        :return: 包含最新读数的字典
        """
        try:
            # 获取传感器数据
            sensor_data = self.data_collector.get_data().get('data', {})
            
            # 尝试获取天气数据
            try:
                weather = self.data_processor.get_weather_data("Beijing")
            except Exception as e:
                logger.warning(f"无法获取天气数据: {e}")
                weather = {
                    "temperature": "N/A",
                    "humidity": "N/A",
                    "condition": "N/A",
                    "precipitation": "N/A"
                }
            
            # 返回组合数据
            return {
                "soil_moisture": sensor_data.get("soil_moisture", "N/A"),
                "temperature": sensor_data.get("temperature", "N/A"),
                "light_intensity": sensor_data.get("light_intensity", "N/A"),
                "rainfall": sensor_data.get("rainfall", "N/A"),
                "weather_temp": weather.get("temperature", "N/A"),
                "weather_humidity": weather.get("humidity", "N/A"),
                "weather_condition": weather.get("condition", "N/A"),
                "weather_precipitation": weather.get("precipitation", "N/A")
            }
        except Exception as e:
            logger.error(f"获取当前读数时出错: {e}", exc_info=True)
            return {
                "soil_moisture": "错误", 
                "temperature": "错误",
                "light_intensity": "错误",
                "rainfall": "错误",
                "weather_temp": "错误",
                "weather_humidity": "错误",
                "weather_condition": "错误",
                "weather_precipitation": "错误"
            }
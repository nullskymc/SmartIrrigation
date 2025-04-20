"""
主程序入口 - 初始化和启动智能灌溉系统
"""
import os
import threading
import time
import schedule
from datetime import datetime
import argparse

# 导入自定义模块
from src.smart_irrigation.logger_config import logger
from src.smart_irrigation.config import config
from src.smart_irrigation.data_collection import DataCollectionModule
from src.smart_irrigation.data_processing import DataProcessingModule
from src.smart_irrigation.ml_model import SoilMoisturePredictor
from src.smart_irrigation.llm_agent import LLMAgentModule
from src.smart_irrigation.control_execution import ControlExecutionModule
from src.smart_irrigation.alarm import AlarmModule
from src.smart_irrigation.ui import UserInterfaceModule
from src.smart_irrigation.models import init_db

def automated_irrigation_check(data_collector, data_processor, llm_agent, control_executor):
    """
    自动灌溉检查任务，定期运行
    
    :param data_collector: 数据采集模块实例
    :param data_processor: 数据处理模块实例
    :param llm_agent: LLM智能体实例
    :param control_executor: 控制执行模块实例
    """
    logger.info("运行自动灌溉检查...")
    try:
        # 采集当前数据
        sensor_data = data_collector.get_data()
        if not sensor_data:
            logger.warning("自动检查未能获取传感器数据")
            return
        
        # 处理数据并获取天气信息
        combined_data = data_processor.process_and_get_weather(sensor_data)
        if not combined_data.get("sensor_data"):
            logger.warning("自动检查未能处理传感器数据")
            return
        
        # 获取当前湿度
        current_humidity = combined_data["sensor_data"].get("data", {}).get("soil_moisture")
        if current_humidity is None:
            logger.warning("自动检查未能获取当前湿度值")
            return
        
        # 预测未来湿度
        try:
            predicted_humidity = llm_agent.predict_humidity(combined_data)
            logger.info(f"当前湿度: {current_humidity}%，预测湿度: {predicted_humidity}%")
        except Exception as e:
            logger.warning(f"湿度预测失败: {e}")
            predicted_humidity = None
        
        # 基于当前数据和预测做决策
        decision = llm_agent.make_decision(current_humidity, predicted_humidity)
        
        # 执行灌溉控制
        if decision.get("control_command") == "start_irrigation" and control_executor.get_status().get("device_status") != "running":
            logger.info(f"自动启动灌溉，原因: {decision.get('reason')}")
            control_executor.start_irrigation()
        elif decision.get("control_command") == "no_action" and control_executor.get_status().get("device_status") == "running":
            # 如果当前正在灌溉，但决策是不需要灌溉，则停止
            # 实际应用中，可能需要更复杂的逻辑，如检查已灌溉时长等
            logger.info("湿度已满足条件，停止灌溉")
            control_executor.stop_irrigation()
        
    except Exception as e:
        logger.error(f"自动灌溉检查过程中发生错误: {e}", exc_info=True)

def run_scheduler():
    """运行调度器，周期执行定时任务"""
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    """主函数：初始化所有模块并启动应用"""
    parser = argparse.ArgumentParser(description="智能灌溉系统")
    parser.add_argument("--init-db", action="store_true", help="初始化数据库")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--no-ui", action="store_true", help="不启动UI界面")
    parser.add_argument("--share", action="store_true", help="生成可分享的Gradio链接")
    args = parser.parse_args()
    
    logger.info("启动智能灌溉系统...")
    
    # 如果指定了配置文件，重新加载配置
    if args.config:
        from src.smart_irrigation.config import Config
        global config
        config = Config(args.config)
    
    # 创建必要的目录
    os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
    
    # 初始化数据库（如果指定）
    if args.init_db:
        logger.info("初始化数据库...")
        init_db()
    
    # 1. 初始化各个模块
    logger.info("初始化模块...")
    data_collector = DataCollectionModule()
    data_processor = DataProcessingModule()
    ml_predictor = SoilMoisturePredictor()
    alarm_module = AlarmModule()
    control_executor = ControlExecutionModule()
    llm_agent = LLMAgentModule(ml_model=ml_predictor, alarm_module=alarm_module)
    ui_module = UserInterfaceModule(llm_agent, control_executor, data_collector, data_processor)
    
    # 2. 设置定时任务
    collection_interval = config.DATA_COLLECTION_INTERVAL_MINUTES
    schedule.every(collection_interval).minutes.do(
        automated_irrigation_check,
        data_collector, data_processor, llm_agent, control_executor
    )
    logger.info(f"已设置自动灌溉检查，每{collection_interval}分钟运行一次")
    
    # 启动调度器线程
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # 3. 启动用户界面
    if not args.no_ui:
        logger.info("启动用户界面...")
        ui_module.launch(share=args.share)
    else:
        logger.info("未启动用户界面，系统以后台模式运行")
        # 保持主线程运行
        try:
            while True:
                time.sleep(60)
                logger.debug(f"系统运行中... {datetime.now()}")
        except KeyboardInterrupt:
            logger.info("接收到停止信号，系统关闭")
    
    logger.info("智能灌溉系统已关闭")

if __name__ == "__main__":
    main()
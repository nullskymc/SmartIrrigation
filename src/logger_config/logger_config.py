"""
日志配置模块 - 配置全局日志记录器
"""
import logging
import os
from src.config import config

def setup_logger(name="IrrigationSystem"):
    """
    配置并返回一个日志记录器实例
    
    :param name: 日志记录器名称
    :return: Logger对象
    """
    # 确保日志文件目录存在
    log_path = os.path.dirname(config.LOG_FILE)
    if log_path and not os.path.exists(log_path):
        os.makedirs(log_path)
    
    # 设置日志格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 获取日志级别
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    # 配置日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 清除已存在的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 添加文件处理器
    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    return logger

# 全局日志记录器实例
logger = setup_logger()
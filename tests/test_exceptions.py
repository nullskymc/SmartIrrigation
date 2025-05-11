"""
异常处理模块的测试
"""
import unittest
import logging
import os
import tempfile
from src.exceptions import *
from src.logger_config import setup_logger

class TestExceptions(unittest.TestCase):
    """测试自定义异常类"""
    
    def test_exception_hierarchy(self):
        """测试异常继承层次"""
        # 测试基础异常类
        base_error = IrrigationSystemError("基础错误")
        self.assertIsInstance(base_error, Exception)
        
        # 测试各个子类异常
        sensor_error = InvalidSensorDataError("传感器数据错误")
        self.assertIsInstance(sensor_error, IrrigationSystemError)
        
        weather_error = WeatherAPIError("天气API错误")
        self.assertIsInstance(weather_error, IrrigationSystemError)
        
        llm_error = LLMCommandError("LLM命令错误")
        self.assertIsInstance(llm_error, IrrigationSystemError)
        
        device_error = IrrigationDeviceError("灌溉设备错误")
        self.assertIsInstance(device_error, IrrigationSystemError)
        
        db_error = DatabaseError("数据库错误")
        self.assertIsInstance(db_error, IrrigationSystemError)
        
        model_error = ModelLoadError("模型加载错误")
        self.assertIsInstance(model_error, IrrigationSystemError)
        
        pred_error = PredictionError("预测错误")
        self.assertIsInstance(pred_error, IrrigationSystemError)
        
        access_error = UnauthorizedAccessError("未授权访问错误")
        self.assertIsInstance(access_error, IrrigationSystemError)
        
    def test_exception_message(self):
        """测试异常消息"""
        message = "测试错误消息"
        error = IrrigationSystemError(message)
        self.assertEqual(str(error), message)

class TestLogger(unittest.TestCase):
    """测试日志记录器"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时日志文件
        self.log_fd, self.log_file = tempfile.mkstemp()
        
        # 备份环境变量
        self.original_env = os.environ.copy()
        os.environ["LOG_FILE"] = self.log_file
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时日志文件
        os.close(self.log_fd)
        os.unlink(self.log_file)
        
        # 恢复环境变量
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_logger_setup(self):
        """测试日志记录器设置"""
        logger = setup_logger("TestLogger")
        
        # 验证日志级别
        self.assertEqual(logger.level, logging.DEBUG)
        
        # 验证处理器数量
        self.assertEqual(len(logger.handlers), 2)  # 文件处理器和控制台处理器
        
        # 找出文件处理器
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break
        
        # 验证文件处理器设置
        self.assertIsNotNone(file_handler)
        self.assertEqual(file_handler.baseFilename, self.log_file)
    
    def test_logger_write(self):
        """测试日志写入"""
        logger = setup_logger("TestLogger")
        
        test_message = "测试日志消息"
        logger.info(test_message)
        
        # 读取日志文件内容
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # 验证消息是否写入
        self.assertIn(test_message, log_content)
        self.assertIn("INFO", log_content)
        self.assertIn("TestLogger", log_content)

if __name__ == "__main__":
    unittest.main()
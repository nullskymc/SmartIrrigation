"""
异常处理模块 - 定义系统特定的异常类
"""

class IrrigationSystemError(Exception):
    """系统基础异常类"""
    pass


class InvalidSensorDataError(IrrigationSystemError):
    """传感器数据无效错误"""
    pass


class WeatherAPIError(IrrigationSystemError):
    """天气API调用错误"""
    pass


class LLMCommandError(IrrigationSystemError):
    """LLM命令解析错误"""
    pass


class IrrigationDeviceError(IrrigationSystemError):
    """灌溉设备控制错误"""
    pass


class DatabaseError(IrrigationSystemError):
    """数据库操作错误"""
    pass


class ModelLoadError(IrrigationSystemError):
    """模型加载错误"""
    pass


class PredictionError(IrrigationSystemError):
    """预测执行错误"""
    pass


class UnauthorizedAccessError(IrrigationSystemError):
    """未授权访问错误"""
    pass
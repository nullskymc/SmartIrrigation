"""
天气查询工具 - 为LangChain Agent提供天气查询能力
"""
from typing import Dict, Any, List
from langchain_core.tools import BaseTool
# 使用langchain-community替代已废弃的导入
from langchain_community.llms import OpenAI
# 这两个我们不需要，先注释掉
# from langchain.agents import AgentType, initialize_agent
# from langchain.chains import LLMChain

from src.data.data_processing import DataProcessingModule
from src.logger_config import logger

class WeatherTool(BaseTool):
    """查询指定城市的天气工具"""
    name: str = "weather_query"
    description: str = "查询指定城市的天气，返回实时天气和天气预报"
    data_processor: DataProcessingModule = None  # 添加为类字段
    
    def __init__(self):
        """初始化天气查询工具"""
        super().__init__()
        self.data_processor = DataProcessingModule()
    
    def _run(self, city: str) -> str:
        """
        执行天气查询
        
        :param city: 城市名称
        :return: 天气信息
        """
        try:
            weather_data = self.data_processor.get_weather_by_city_name(city)
            result = []
            
            if not weather_data:
                return f"无法获取 {city} 的天气信息"
                
            if weather_data.get("lives"):
                lives = weather_data["lives"]
                result.append(f"📍 {lives.get('province')} {lives.get('city')} 实况天气")
                result.append(f"🌡️ 温度: {lives.get('temperature')}°C")
                result.append(f"☁️ 天气: {lives.get('weather')}")
                result.append(f"💧 湿度: {lives.get('humidity')}%")
                result.append(f"🧭 风向: {lives.get('winddirection')}")
                result.append(f"💨 风力: {lives.get('windpower')}")
                result.append(f"🕒 发布时间: {lives.get('reporttime')}")
                result.append("")
                
            if weather_data.get("forecast") and len(weather_data["forecast"]) > 0:
                result.append(f"📅 天气预报 (未来{len(weather_data['forecast'])}天):")
                for i, day in enumerate(weather_data["forecast"]):
                    result.append(f"  第{i+1}天 ({day.get('date')}):")
                    result.append(f"    ☀️ 白天: {day.get('dayweather')}, {day.get('daytemp')}°C, {day.get('daywind')}风{day.get('daypower')}")
                    result.append(f"    🌙 夜间: {day.get('nightweather')}, {day.get('nighttemp')}°C, {day.get('nightwind')}风{day.get('nightpower')}")
            
            return "\n".join(result)
        except Exception as e:
            logger.error(f"获取天气数据失败: {str(e)}", exc_info=True)
            return f"查询天气时出错: {str(e)}"
    
    def _arun(self, city: str) -> str:
        """异步运行（仅为兼容API，实际同步执行）"""
        return self._run(city)


# 在这里注册工具到LangChain工具库
def register_weather_tools():
    """注册天气查询工具到工具库"""
    return [WeatherTool()]


# 命令解析函数
def parse_weather_command(command: str) -> Dict[str, Any]:
    """
    解析天气查询命令
    
    :param command: 用户输入的命令
    :return: 解析结果字典 {'action': 'weather_query', 'city': '城市名'}
    """
    lower_cmd = command.lower()
    keywords = ["天气", "weather", "查询", "query", "气象", "温度", "预报"]
    
    # 检查是否是天气查询命令
    is_weather_query = any(keyword in lower_cmd for keyword in keywords)
    if not is_weather_query:
        return None
        
    # 提取城市名
    city = "北京"  # 默认城市
    common_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "重庆", "武汉", "西安", "天津"]
    
    # 尝试从命令中提取城市名
    for c in common_cities:
        if c in command:
            city = c
            break
    
    return {"action": "weather_query", "city": city}

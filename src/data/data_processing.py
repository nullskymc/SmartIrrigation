"""
数据处理模块 - 处理传感器数据并获取相关的天气信息
"""
import requests
import datetime
from typing import Dict, Any, Optional

from src.logger_config import logger
from src.config import config
from src.exceptions import WeatherAPIError, InvalidSensorDataError

class DataProcessingModule:
    """
    处理传感器数据并获取相关的天气信息
    """
    def __init__(self, api_key: str = None, api_url: str = None):
        """
        初始化模块，保存天气API密钥
        
        :param api_key: 天气API密钥，如果为None则使用配置中的密钥
        :param api_url: 天气API URL，如果为None则使用配置中的URL
        """
        self.api_key = api_key or config.WEATHER_API_KEY
        self.weather_api_url = api_url or config.API_SERVICE_URL
        logger.info("DataProcessingModule initialized.")
    
    def process_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗和验证传感器数据
        
        :param sensor_data: 原始传感器数据字典
        :return: 清洗后的传感器数据字典，可能添加状态字段
        :raises: InvalidSensorDataError 如果数据无效
        """
        if not sensor_data or not isinstance(sensor_data, dict):
            raise InvalidSensorDataError("Sensor data is None or not a dictionary")
        
        logger.debug(f"Processing sensor data for {sensor_data.get('sensor_id')}")
        
        # 实现数据清洗逻辑：检查范围、处理缺失值等
        processed_data = sensor_data.copy()
        processed_data["status"] = "processed"  # 添加处理状态
        
        data = processed_data.get("data", {})
        if not data:
            processed_data["status"] = "invalid_data"
            raise InvalidSensorDataError("No data field in sensor data")
        
        # 验证各个数据字段的有效性
        soil_moisture = data.get("soil_moisture")
        if soil_moisture is None or not (0 <= soil_moisture <= 100):
            logger.warning(f"Invalid soil moisture value: {soil_moisture}")
            processed_data["status"] = "invalid_data"
            # 可以选择修正或标记无效
            data["soil_moisture"] = max(0, min(100, soil_moisture if soil_moisture is not None else 0))
        
        temperature = data.get("temperature")
        if temperature is not None and (temperature < -40 or temperature > 60):
            logger.warning(f"Unusual temperature value: {temperature}")
            processed_data["status"] = "suspicious_data"
        
        # 对于缺失的数据，可以填充默认值或前一次的值
        for key in ["soil_moisture", "temperature", "light_intensity", "rainfall"]:
            if key not in data or data[key] is None:
                data[key] = 0.0
                logger.warning(f"Missing {key} value, setting to default 0.0")
        
        return processed_data
    
    def get_weather_data(self, location: str = "Tokyo") -> Dict[str, Any]:
        """
        调用天气API获取指定地点的天气信息
        
        :param location: 地点名称或坐标
        :return: 天气数据字典
        :raises: WeatherAPIError 如果API调用失败
        """
        if not self.api_key:
            logger.warning("Weather API key not set, cannot fetch weather data")
            raise WeatherAPIError("Weather API key not configured")
        
        params = {'q': location, 'appid': self.api_key, 'units': 'metric'}
        try:
            logger.info(f"Fetching weather data for {location}")
            response = requests.get(self.weather_api_url, params=params, timeout=10)
            response.raise_for_status()  # 如果HTTP状态码是4xx或5xx，则抛出异常
            
            weather_data = response.json()
            
            # 提取需要的字段
            extracted_data = {
                "location": weather_data.get('name'),
                "temperature": weather_data.get('main', {}).get('temp'),
                "humidity": weather_data.get('main', {}).get('humidity'),
                "wind_speed": weather_data.get('wind', {}).get('speed'),
                "condition": weather_data.get('weather', [{}])[0].get('description'),
                "precipitation": weather_data.get('rain', {}).get('1h', 0),
                "timestamp": datetime.datetime.now().isoformat(),
                "forecast": []  # 简化版不包含预报
            }
            
            logger.debug(f"Fetched weather data for {location}: {extracted_data}")
            return extracted_data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching weather data for {location}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise WeatherAPIError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error processing weather data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise WeatherAPIError(error_msg) from e
    
    def process_and_get_weather(self, sensor_data: Dict[str, Any], location: str = "Tokyo") -> Dict[str, Any]:
        """
        组合处理传感器数据和获取天气数据
        
        :param sensor_data: 原始传感器数据
        :param location: 地点
        :return: 包含处理后传感器数据和天气数据的字典
        """
        result = {"sensor_data": None, "weather_data": None}
        
        # 处理传感器数据
        try:
            processed_sensor_data = self.process_sensor_data(sensor_data)
            result["sensor_data"] = processed_sensor_data
        except InvalidSensorDataError as e:
            logger.error(f"Invalid sensor data: {str(e)}")
            # 保留原始数据，但标记为无效
            if sensor_data:
                sensor_data_copy = sensor_data.copy()
                sensor_data_copy["status"] = "invalid"
                result["sensor_data"] = sensor_data_copy
        
        # 获取天气数据
        try:
            weather_data = self.get_weather_data(location)
            result["weather_data"] = weather_data
            
            # 可选：将天气数据存入数据库
            # self._store_weather_data(weather_data, db)
            
        except WeatherAPIError as e:
            logger.warning(f"Could not fetch weather data: {str(e)}")
            # 继续处理，但天气数据为空
        
        return result
    
    def _store_weather_data(self, weather_data: Dict[str, Any], db):
        """
        将天气数据存储到数据库
        
        :param weather_data: 天气数据字典
        :param db: 数据库会话
        :return: 存储的数据库对象
        """
        if db is None:
            return None
        
        from src.database.models import WeatherData
        
        try:
            timestamp = datetime.datetime.fromisoformat(weather_data["timestamp"]) \
                if isinstance(weather_data["timestamp"], str) else weather_data["timestamp"]
            
            db_weather = WeatherData(
                location=weather_data.get("location", "unknown"),
                timestamp=timestamp,
                temperature=weather_data.get("temperature"),
                humidity=weather_data.get("humidity"),
                wind_speed=weather_data.get("wind_speed"),
                condition=weather_data.get("condition"),
                precipitation=weather_data.get("precipitation", 0),
                forecast_data=weather_data
            )
            
            db.add(db_weather)
            db.commit()
            db.refresh(db_weather)
            logger.info(f"Stored weather data for {weather_data.get('location')} to database")
            return db_weather
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing weather data: {str(e)}", exc_info=True)
            return None
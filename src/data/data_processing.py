"""
数据处理模块 - 处理传感器数据并获取相关的天气信息
"""
import requests
import datetime
from typing import Dict, Any, Optional

from src.logger_config import logger
from src.config import config
from src.exceptions.exceptions import WeatherAPIError, InvalidSensorDataError

class DataProcessingModule:
    """
    处理传感器数据并获取相关的天气信息
    """
    # 常用城市编码映射表
    CITY_CODE_MAP = {
        "北京": "110000",
        "上海": "310000",
        "广州": "440100",
        "深圳": "440300",
        "杭州": "330100",
        "南京": "320100",
        "武汉": "420100",
        "成都": "510100",
        "重庆": "500000",
        "西安": "610100",
        "天津": "120000",
    }
    
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
    
    def get_weather_data(self, city: str = "110101") -> Dict[str, Any]:
        """
        调用高德地图天气API获取指定城市的天气信息
        
        :param city: 城市编码(adcode)，默认为北京市-东城区(110101)
        :return: 天气数据字典
        :raises: WeatherAPIError 如果API调用失败
        """
        if not self.api_key or self.api_key == "None" or self.api_key == "":
            logger.warning("Weather API key not set, cannot fetch weather data")
            raise WeatherAPIError("Weather API key not configured")
        
        extracted_data = {
            "adcode": city,
            "timestamp": datetime.datetime.now().isoformat(),
            "lives": None,
            "forecast": []
        }
        
        # 1. 获取实况天气 - extensions=base
        live_params = {
            'key': self.api_key,
            'city': city,
            'extensions': 'base',  # 获取实况天气
            'output': 'JSON'
        }
        
        try:
            logger.info(f"Fetching live weather data for city code {city}")
            live_response = requests.get(self.weather_api_url, params=live_params, timeout=10)
            live_response.raise_for_status()
            
            live_data = live_response.json()
            
            # 检查API响应状态
            if live_data.get('status') != '1':
                error_msg = f"实况天气API请求失败: {live_data.get('info')}, 错误码: {live_data.get('infocode')}"
                logger.error(error_msg)
                # 不立即抛出异常，尝试获取预报天气
                del extracted_data["lives"]  # 删除lives键，表示没有实况天气数据
            else:
                # 从响应中提取实况天气数据
                lives = live_data.get('lives', [])
                if lives:
                    extracted_data["lives"] = lives[0]  # 获取第一个城市的实况天气
                    extracted_data["city"] = lives[0].get('city')
                    extracted_data["province"] = lives[0].get('province')
                else:
                    del extracted_data["lives"]  # 如果没有lives数据则删除该键
        
        except Exception as e:
            logger.error(f"Error fetching live weather data: {str(e)}")
            # 继续尝试获取预报天气
        
        # 2. 获取预报天气 - extensions=all
        forecast_params = {
            'key': self.api_key,
            'city': city,
            'extensions': 'all',  # 获取预报天气
            'output': 'JSON'
        }
        
        try:
            logger.info(f"Fetching forecast weather data for city code {city}")
            forecast_response = requests.get(self.weather_api_url, params=forecast_params, timeout=10)
            forecast_response.raise_for_status()
            
            forecast_data = forecast_response.json()
            
            # 检查API响应状态
            if forecast_data.get('status') != '1':
                error_msg = f"预报天气API请求失败: {forecast_data.get('info')}, 错误码: {forecast_data.get('infocode')}"
                logger.error(error_msg)
                # 如果实况天气和预报天气都失败，抛出异常
                if not extracted_data.get("lives"):
                    raise WeatherAPIError(error_msg)
            else:
                # 从响应中提取预报天气数据
                forecasts = forecast_data.get('forecasts', [])
                if forecasts:
                    forecast_item = forecasts[0]  # 获取第一个城市的预报
                    
                    # 如果实况天气请求失败，则使用预报中的城市信息
                    if not extracted_data.get("city"):
                        extracted_data["city"] = forecast_item.get('city')
                        extracted_data["province"] = forecast_item.get('province')
                    
                    extracted_data["reporttime"] = forecast_item.get('reporttime')
                    extracted_data["forecast"] = forecast_item.get('casts', [])
            
            logger.debug(f"Fetched weather data for city code {city}: {extracted_data}")
            return extracted_data
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching forecast weather data for city code {city}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 如果至少有实况天气数据，返回已有数据
            if extracted_data.get("lives"):
                logger.warning("Using only live weather data due to forecast fetch error")
                return extracted_data
            
            raise WeatherAPIError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error processing weather data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 如果至少有实况天气数据，返回已有数据
            if extracted_data.get("lives"):
                logger.warning("Using only live weather data due to processing error")
                return extracted_data
                
            raise WeatherAPIError(error_msg) from e
    
    def process_and_get_weather(self, sensor_data: Dict[str, Any], city: str = "110101") -> Dict[str, Any]:
        """
        组合处理传感器数据和获取天气数据
        
        :param sensor_data: 原始传感器数据
        :param city: 城市编码(adcode)，默认为北京市-东城区(110101)
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
            weather_data = self.get_weather_data(city)
            result["weather_data"] = weather_data
            
            # 可选：将天气数据存入数据库
            # self._store_weather_data(weather_data, db)
            
        except WeatherAPIError as e:
            logger.warning(f"Could not fetch weather data: {str(e)}")
            # 继续处理，但天气数据为空
        
        return result
    
    def city_to_code(self, city_name: str) -> str:
        """
        将城市名称转换为高德地图的城市编码(adcode)
        
        :param city_name: 城市名称，如"北京"、"上海"等
        :return: 城市编码，默认返回北京的编码("110000")
        """
        # 首先尝试直接从映射表中获取
        if city_name in self.CITY_CODE_MAP:
            logger.debug(f"City code for {city_name} found in map: {self.CITY_CODE_MAP[city_name]}")
            return self.CITY_CODE_MAP[city_name]
        
        # 如果没有在映射表中找到，可以尝试调用高德地图的地理编码API
        # 这里简化处理，仅查找预定义的城市
        logger.warning(f"城市 '{city_name}' 编码未找到，使用默认编码(北京)")
        return "110000"  # 默认返回北京的编码
    
    def get_weather_by_city_name(self, city_name: str) -> Dict[str, Any]:
        """
        通过城市名称获取天气数据
        
        :param city_name: 城市名称，如"北京"、"上海"等
        :return: 天气数据字典
        :raises: WeatherAPIError 如果API调用失败
        """
        city_code = self.city_to_code(city_name)
        return self.get_weather_data(city_code)
    
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
            
            # 优先使用实况天气数据，如果没有则使用预报
            lives_data = weather_data.get("lives", {})
            current_forecast = weather_data.get("forecast", [])[0] if weather_data.get("forecast") else {}
            
            if lives_data:
                # 使用实况天气数据
                db_weather = WeatherData(
                    location=lives_data.get("city", "unknown"),
                    timestamp=timestamp,
                    temperature=lives_data.get("temperature"),  # 实时温度
                    humidity=lives_data.get("humidity"),  # 实况湿度
                    wind_speed=lives_data.get("windpower"),  # 风力等级
                    condition=lives_data.get("weather"),  # 天气状况
                    precipitation=0,  # 高德地图API不直接提供降水量
                    forecast_data=weather_data
                )
            else:
                # 使用预报天气数据
                db_weather = WeatherData(
                    location=weather_data.get("city", "unknown"),
                    timestamp=timestamp,
                    temperature=current_forecast.get("daytemp"),  # 白天温度
                    humidity=None,  # 高德地图API预报不提供湿度信息
                    wind_speed=current_forecast.get("daypower"),  # 风力等级
                    condition=current_forecast.get("dayweather"),  # 天气状况
                    precipitation=0,  # 高德地图API不直接提供降水量
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
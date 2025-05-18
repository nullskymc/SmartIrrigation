"""
数据处理模块的测试
"""
import unittest
from unittest.mock import patch, MagicMock
import datetime
import json
from src.data.data_processing import DataProcessingModule
from src.exceptions.exceptions import InvalidSensorDataError, WeatherAPIError

class TestDataProcessingModule(unittest.TestCase):
    """测试数据处理模块"""
    
    def setUp(self):
        """测试前准备"""
        self.api_key = "test_api_key"
        self.api_url = "http://test-api.example.com"
        self.processing_module = DataProcessingModule(api_key=self.api_key, api_url=self.api_url)
        
        # 创建有效的传感器数据
        self.valid_sensor_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "sensor_id": "test-sensor-1",
            "data": {
                "soil_moisture": 50.0,
                "temperature": 25.0,
                "light_intensity": 800.0,
                "rainfall": 0.0
            }
        }
    
    def test_init(self):
        """测试初始化"""
        # 验证API密钥和URL正确设置
        self.assertEqual(self.processing_module.api_key, self.api_key)
        self.assertEqual(self.processing_module.weather_api_url, self.api_url)
        
        # 测试默认配置
        with patch('src.data.data_processing.config') as mock_config:
            mock_config.WEATHER_API_KEY = "default_key"
            mock_config.API_SERVICE_URL = "default_url"
            module = DataProcessingModule()
            self.assertEqual(module.api_key, "default_key")
            self.assertEqual(module.weather_api_url, "default_url")
    
    def test_process_sensor_data_valid(self):
        """测试处理有效的传感器数据"""
        processed_data = self.processing_module.process_sensor_data(self.valid_sensor_data)
        
        # 验证处理结果
        self.assertEqual(processed_data["status"], "processed")
        self.assertEqual(processed_data["sensor_id"], self.valid_sensor_data["sensor_id"])
        self.assertEqual(processed_data["data"]["soil_moisture"], self.valid_sensor_data["data"]["soil_moisture"])
    
    def test_process_sensor_data_invalid(self):
        """测试处理无效的传感器数据"""
        # 测试None数据
        with self.assertRaises(InvalidSensorDataError):
            self.processing_module.process_sensor_data(None)
        
        # 测试空字典
        with self.assertRaises(InvalidSensorDataError):
            self.processing_module.process_sensor_data({})
        
        # 测试缺少数据字段
        invalid_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "sensor_id": "test-sensor-1",
            # 缺少data字段
        }
        with self.assertRaises(InvalidSensorDataError):
            self.processing_module.process_sensor_data(invalid_data)
    
    def test_process_sensor_data_abnormal(self):
        """测试处理异常值的传感器数据"""
        # 异常的土壤湿度值
        abnormal_data = self.valid_sensor_data.copy()
        abnormal_data["data"] = abnormal_data["data"].copy()
        abnormal_data["data"]["soil_moisture"] = 150.0  # 超出正常范围
        
        processed_data = self.processing_module.process_sensor_data(abnormal_data)
        # 验证异常值被截断到有效范围内
        self.assertEqual(processed_data["data"]["soil_moisture"], 100.0)
        self.assertEqual(processed_data["status"], "invalid_data")
        
        # 异常的温度值
        abnormal_data = self.valid_sensor_data.copy()
        abnormal_data["data"] = abnormal_data["data"].copy()
        abnormal_data["data"]["temperature"] = 70.0  # 不太可能的高温
        
        processed_data = self.processing_module.process_sensor_data(abnormal_data)
        # 验证被标记为可疑数据
        self.assertEqual(processed_data["status"], "suspicious_data")
    
    def test_process_sensor_data_missing_fields(self):
        """测试处理缺失字段的传感器数据"""
        missing_fields_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "sensor_id": "test-sensor-1",
            "data": {
                # 缺少部分字段
                "soil_moisture": 50.0
                # 没有temperature, light_intensity, rainfall
            }
        }
        
        processed_data = self.processing_module.process_sensor_data(missing_fields_data)
        
        # 验证缺失字段被填充为默认值
        self.assertEqual(processed_data["data"]["temperature"], 0.0)
        self.assertEqual(processed_data["data"]["light_intensity"], 0.0)
        self.assertEqual(processed_data["data"]["rainfall"], 0.0)
    
    @patch('src.data.data_processing.requests.get')
    def test_get_weather_data_success(self, mock_get):
        """测试成功获取天气数据"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Tokyo",
            "main": {
                "temp": 22.5,
                "humidity": 65
            },
            "wind": {
                "speed": 3.2
            },
            "weather": [
                {"description": "晴天"}
            ],
            "rain": {
                "1h": 0.0
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # 获取天气数据
        weather_data = self.processing_module.get_weather_data("Tokyo")
        
        # 验证请求参数
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["q"], "Tokyo")
        self.assertEqual(kwargs["params"]["appid"], self.api_key)
        
        # 验证返回数据
        self.assertEqual(weather_data["location"], "Tokyo")
        self.assertEqual(weather_data["temperature"], 22.5)
        self.assertEqual(weather_data["humidity"], 65)
        self.assertEqual(weather_data["wind_speed"], 3.2)
        self.assertEqual(weather_data["condition"], "晴天")
        self.assertEqual(weather_data["precipitation"], 0.0)
    
    @patch('src.data.data_processing.requests.get')
    def test_get_weather_data_api_error(self, mock_get):
        """测试天气API错误处理"""
        # 模拟API请求失败
        mock_get.side_effect = Exception("API连接错误")
        
        # 验证异常被正确抛出和转换
        with self.assertRaises(WeatherAPIError):
            self.processing_module.get_weather_data("Tokyo")
    
    def test_get_weather_data_no_api_key(self):
        """测试没有API密钥的情况"""
        module = DataProcessingModule(api_key=None)
        
        with self.assertRaises(WeatherAPIError):
            module.get_weather_data("Tokyo")
    
    @patch('src.data.data_processing.DataProcessingModule.process_sensor_data')
    @patch('src.data.data_processing.DataProcessingModule.get_weather_data')
    def test_process_and_get_weather(self, mock_get_weather, mock_process_sensor):
        """测试组合处理流程"""
        # 模拟方法返回值
        mock_process_sensor.return_value = {
            "status": "processed",
            "sensor_id": "test-sensor-1",
            "data": {"soil_moisture": 50.0}
        }
        mock_get_weather.return_value = {
            "location": "Tokyo",
            "temperature": 25.0,
            "humidity": 60.0
        }
        
        # 调用测试方法
        result = self.processing_module.process_and_get_weather(self.valid_sensor_data, "Tokyo")
        
        # 验证子方法调用
        mock_process_sensor.assert_called_once_with(self.valid_sensor_data)
        mock_get_weather.assert_called_once_with("Tokyo")
        
        # 验证返回结果
        self.assertEqual(result["sensor_data"]["status"], "processed")
        self.assertEqual(result["weather_data"]["location"], "Tokyo")
    
    @patch('src.data.data_processing.DataProcessingModule.process_sensor_data')
    @patch('src.data.data_processing.DataProcessingModule.get_weather_data')
    def test_process_and_get_weather_with_errors(self, mock_get_weather, mock_process_sensor):
        """测试组合处理流程中的错误处理"""
        # 模拟传感器数据处理错误
        mock_process_sensor.side_effect = InvalidSensorDataError("无效数据")
        
        # 模拟天气API错误
        mock_get_weather.side_effect = WeatherAPIError("API错误")
        
        # 调用测试方法
        result = self.processing_module.process_and_get_weather(self.valid_sensor_data, "Tokyo")
        
        # 验证即使有错误，方法仍然返回结果
        self.assertIsNotNone(result)
        # 验证无效数据被标记
        self.assertEqual(result["sensor_data"]["status"], "invalid")
        # 验证天气数据为None
        self.assertIsNone(result["weather_data"])
    
    @patch('src.database.models.WeatherData')
    def test_store_weather_data(self, mock_weather_data):
        """测试存储天气数据到数据库"""
        mock_db = MagicMock()
        weather_data = {
            "location": "Tokyo",
            "timestamp": datetime.datetime.now().isoformat(),
            "temperature": 25.0,
            "humidity": 60.0,
            "wind_speed": 3.2,
            "condition": "晴天",
            "precipitation": 0.0
        }
        self.processing_module._store_weather_data(weather_data, mock_db)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_city_to_code(self):
        """测试城市名称到编码的转换"""
        # 测试已知城市
        self.assertEqual(self.processing_module.city_to_code("北京"), "110000")
        self.assertEqual(self.processing_module.city_to_code("上海"), "310000")
        
        # 测试未知城市，应返回默认值
        self.assertEqual(self.processing_module.city_to_code("未知城市"), "110000")
    
    @patch('requests.get')
    def test_get_weather_data(self, mock_get):
        """测试获取天气数据"""
        # Mock 模拟成功响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "1",
            "count": "1",
            "info": "OK",
            "infocode": "10000",
            "lives": [{
                "province": "北京",
                "city": "朝阳区",
                "adcode": "110105",
                "weather": "晴",
                "temperature": "26",
                "winddirection": "西南",
                "windpower": "≤3",
                "humidity": "46",
                "reporttime": "2023-05-18 10:28:14"
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # 调用方法
        weather_data = self.processing_module.get_weather_data("110105")
        
        # 验证获取到的数据
        self.assertEqual(weather_data["adcode"], "110105")
        self.assertIn("lives", weather_data)
        self.assertEqual(weather_data["lives"]["city"], "朝阳区")
        self.assertEqual(weather_data["lives"]["temperature"], "26")
    
    @patch('requests.get')
    def test_get_weather_data_forecast(self, mock_get):
        """测试获取天气预报数据"""
        # 首先Mock实况天气
        live_response = MagicMock()
        live_response.json.return_value = {
            "status": "1",
            "info": "OK",
            "infocode": "10000",
            "lives": [{
                "province": "北京",
                "city": "朝阳区",
                "adcode": "110105",
                "weather": "晴",
                "temperature": "26",
                "humidity": "46"
            }]
        }
        
        # 然后Mock预报天气
        forecast_response = MagicMock()
        forecast_response.json.return_value = {
            "status": "1",
            "info": "OK",
            "infocode": "10000",
            "forecasts": [{
                "city": "朝阳区",
                "adcode": "110105",
                "province": "北京",
                "reporttime": "2023-05-18 11:00:00",
                "casts": [
                    {
                        "date": "2023-05-18",
                        "week": "4",
                        "dayweather": "晴",
                        "nightweather": "多云",
                        "daytemp": "30",
                        "nighttemp": "18"
                    },
                    {
                        "date": "2023-05-19",
                        "week": "5",
                        "dayweather": "多云",
                        "nightweather": "小雨",
                        "daytemp": "28",
                        "nighttemp": "17"
                    }
                ]
            }]
        }
        
        # 设置两次请求的不同响应
        mock_get.side_effect = [live_response, forecast_response]
        
        # 调用方法
        weather_data = self.processing_module.get_weather_data("110105")
        
        # 验证获取到的数据
        self.assertEqual(weather_data["adcode"], "110105")
        self.assertIn("lives", weather_data)
        self.assertIn("forecast", weather_data)
        self.assertEqual(len(weather_data["forecast"]), 2)
        self.assertEqual(weather_data["forecast"][0]["daytemp"], "30")
    
    @patch('src.data.data_processing.DataProcessingModule.get_weather_data')
    def test_get_weather_by_city_name(self, mock_get_weather):
        """测试通过城市名称获取天气"""
        # 设置模拟返回值
        mock_get_weather.return_value = {
            "adcode": "110000",
            "city": "北京市",
            "lives": {"temperature": "25", "weather": "晴"},
            "forecast": []
        }
        
        # 调用方法
        weather = self.processing_module.get_weather_by_city_name("北京")
        
        # 验证是否使用了正确的城市编码调用get_weather_data
        mock_get_weather.assert_called_once_with("110000")
        
        # 验证返回的数据
        self.assertEqual(weather["adcode"], "110000")
        self.assertEqual(weather["city"], "北京市")
    
    @patch('requests.get')
    def test_api_error_handling(self, mock_get):
        """测试API错误处理"""
        # Mock 请求失败的响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "0",
            "info": "INVALID_USER_KEY",
            "infocode": "10001"
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # 测试处理API错误
        with self.assertRaises(WeatherAPIError):
            self.processing_module.get_weather_data("110105")

if __name__ == "__main__":
    unittest.main()
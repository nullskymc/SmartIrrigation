"""
数据处理模块的天气API测试
"""
import unittest
import datetime
from unittest.mock import patch, MagicMock
from src.data.data_processing import DataProcessingModule
from src.exceptions.exceptions import WeatherAPIError

class TestWeatherAPI(unittest.TestCase):
    """测试高德天气API功能"""

    def setUp(self):
        """测试前准备"""
        self.api_key = "test_api_key"
        self.api_url = "http://test-api.example.com"
        self.processing_module = DataProcessingModule(api_key=self.api_key, api_url=self.api_url)

    def test_city_to_code(self):
        """测试城市名称到编码的转换"""
        # 测试已知城市
        self.assertEqual(self.processing_module.city_to_code("北京"), "110000")
        self.assertEqual(self.processing_module.city_to_code("上海"), "310000")
        
        # 测试未知城市，应返回默认值
        self.assertEqual(self.processing_module.city_to_code("未知城市"), "110000")

    @patch('requests.get')
    def test_get_weather_data(self, mock_get):
        """测试获取天气数据 - 仅返回实况天气"""
        # Mock 实况天气API响应
        mock_live_response = MagicMock()
        mock_live_response.json.return_value = {
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
        mock_live_response.raise_for_status = MagicMock()
        
        # Mock 预报天气API响应 - 状态码不为1
        mock_forecast_response = MagicMock()
        mock_forecast_response.json.return_value = {
            "status": "1",  # 成功状态
            "info": "OK",
            "infocode": "10000",
            "forecasts": []  # 空预报
        }
        mock_forecast_response.raise_for_status = MagicMock()
        
        # 设置两次请求的不同响应
        mock_get.side_effect = [mock_live_response, mock_forecast_response]
        
        # 调用方法
        weather_data = self.processing_module.get_weather_data("110105")
        
        # 验证获取到的数据 - 有实况天气，没有预报
        self.assertEqual(weather_data["adcode"], "110105")
        self.assertIn("lives", weather_data)
        self.assertEqual(weather_data["lives"]["city"], "朝阳区")
        self.assertEqual(weather_data["lives"]["temperature"], "26")
        self.assertEqual(len(weather_data["forecast"]), 0)  # 预报为空
    
    @patch('requests.get')
    def test_get_weather_data_with_forecast(self, mock_get):
        """测试获取天气数据 - 同时返回实况和预报天气"""
        # Mock 实况天气API响应
        mock_live_response = MagicMock()
        mock_live_response.json.return_value = {
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
        mock_live_response.raise_for_status = MagicMock()
        
        # Mock 预报天气API响应
        mock_forecast_response = MagicMock()
        mock_forecast_response.json.return_value = {
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
                        "nighttemp": "18",
                        "daywind": "南",
                        "nightwind": "南",
                        "daypower": "≤3",
                        "nightpower": "≤3"
                    },
                    {
                        "date": "2023-05-19",
                        "week": "5",
                        "dayweather": "多云",
                        "nightweather": "小雨",
                        "daytemp": "28",
                        "nighttemp": "17",
                        "daywind": "南",
                        "nightwind": "南",
                        "daypower": "≤3",
                        "nightpower": "≤3"
                    }
                ]
            }]
        }
        mock_forecast_response.raise_for_status = MagicMock()
        
        # 设置两次请求的不同响应
        mock_get.side_effect = [mock_live_response, mock_forecast_response]
        
        # 调用方法
        weather_data = self.processing_module.get_weather_data("110105")
        
        # 验证获取到的数据
        self.assertEqual(weather_data["adcode"], "110105")
        self.assertIn("lives", weather_data)
        self.assertEqual(weather_data["lives"]["city"], "朝阳区")
        self.assertEqual(weather_data["lives"]["temperature"], "26")
        self.assertIn("forecast", weather_data)
        self.assertEqual(len(weather_data["forecast"]), 2)  # 有两天的预报
        self.assertEqual(weather_data["forecast"][0]["daytemp"], "30")
        self.assertEqual(weather_data["forecast"][1]["dayweather"], "多云")

    @patch('requests.get')
    def test_get_weather_data_only_forecast(self, mock_get):
        """测试只获取到预报天气的情况"""
        # Mock 实况天气API响应失败
        mock_live_response = MagicMock()
        mock_live_response.json.return_value = {
            "status": "0",  # 失败状态
            "info": "INVALID_USER_KEY",
            "infocode": "10001"
        }
        mock_live_response.raise_for_status = MagicMock()
        
        # Mock 预报天气API响应成功
        mock_forecast_response = MagicMock()
        mock_forecast_response.json.return_value = {
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
                        "dayweather": "晴",
                        "daytemp": "30"
                    }
                ]
            }]
        }
        mock_forecast_response.raise_for_status = MagicMock()
        
        # 设置两次请求的响应
        mock_get.side_effect = [mock_live_response, mock_forecast_response]
        
        # 调用方法
        weather_data = self.processing_module.get_weather_data("110105")
        
        # 验证获取到的数据
        self.assertEqual(weather_data["adcode"], "110105")
        self.assertNotIn("lives", weather_data)  # 没有实况天气
        self.assertIn("forecast", weather_data)
        self.assertEqual(weather_data["city"], "朝阳区")  # 从预报中获取城市信息
        self.assertEqual(len(weather_data["forecast"]), 1)

    @patch('requests.get')
    def test_get_weather_data_api_error(self, mock_get):
        """测试两个API都失败的情况"""
        # 两个API都返回失败
        mock_live_response = MagicMock()
        mock_live_response.json.return_value = {
            "status": "0",
            "info": "INVALID_USER_KEY",
            "infocode": "10001"
        }
        mock_live_response.raise_for_status = MagicMock()
        
        mock_forecast_response = MagicMock()
        mock_forecast_response.json.return_value = {
            "status": "0",
            "info": "INVALID_USER_KEY",
            "infocode": "10001"
        }
        mock_forecast_response.raise_for_status = MagicMock()
        
        mock_get.side_effect = [mock_live_response, mock_forecast_response]
        
        # 应抛出异常
        with self.assertRaises(WeatherAPIError):
            self.processing_module.get_weather_data("110105")

    @patch('requests.get')
    def test_get_weather_data_http_error(self, mock_get):
        """测试HTTP错误处理"""
        # 模拟HTTP错误
        mock_get.side_effect = Exception("网络连接错误")
        
        # 应抛出异常
        with self.assertRaises(WeatherAPIError):
            self.processing_module.get_weather_data("110105")

    def test_get_weather_data_no_api_key(self):
        """测试没有API密钥的情况"""
        # 创建没有API密钥的模块，并完全禁用正常的初始化过程
        with patch('src.data.data_processing.config', spec=True) as mock_config:
            # 确保config.WEATHER_API_KEY返回空字符串
            mock_config.WEATHER_API_KEY = ""
            module = DataProcessingModule()
            print(f"DEBUG - API KEY: '{module.api_key}'")  # 调试信息
            
            # 应抛出异常
            with self.assertRaises(WeatherAPIError):
                module.get_weather_data("110105")

    @patch('src.data.data_processing.DataProcessingModule.get_weather_data')
    def test_get_weather_by_city_name(self, mock_get_weather):
        """测试通过城市名称获取天气"""
        # 模拟返回值
        mock_get_weather.return_value = {
            "adcode": "110000",
            "city": "北京市",
            "lives": {"temperature": "25", "weather": "晴"},
            "forecast": []
        }
        
        # 调用方法
        weather = self.processing_module.get_weather_by_city_name("北京")
        
        # 验证调用参数和返回值
        mock_get_weather.assert_called_once_with("110000")
        self.assertEqual(weather["adcode"], "110000")
        self.assertEqual(weather["city"], "北京市")

if __name__ == "__main__":
    unittest.main()

# SmartIrrigation 天气查询模块使用文档

本文档介绍如何使用 SmartIrrigation 项目中的天气查询功能。该功能基于高德地图天气API，能够获取中国各城市的实时天气和未来天气预报。

## 配置说明

天气API需要高德地图的API密钥才能正常工作。请按照以下步骤配置：

1. 前往[高德开放平台](https://lbs.amap.com/api/webservice/guide/api/weatherinfo)注册账号
2. 创建应用并申请Web服务API密钥
3. 将获取的API密钥填入项目的 `config.yaml` 文件中：

```yaml
# API配置
apis:
  weather_api_key: "您的高德地图API密钥"
  weather_service_url: "https://restapi.amap.com/v3/weather/weatherInfo"
```

## 使用示例

### 在代码中使用

```python
from src.data.data_processing import DataProcessingModule

# 初始化数据处理模块
data_processor = DataProcessingModule()

# 通过城市编码获取天气（高德地图adcode）
weather_data = data_processor.get_weather_data("110101")  # 北京市-东城区

# 通过城市名称获取天气
weather_data = data_processor.get_weather_by_city_name("北京")

# 处理返回的天气数据
if weather_data.get("lives"):
    print(f"实况天气 - {weather_data['lives'].get('city')}:")
    print(f"温度: {weather_data['lives'].get('temperature')}°C")
    print(f"天气: {weather_data['lives'].get('weather')}")

# 查看天气预报
for forecast in weather_data.get("forecast", []):
    print(f"日期: {forecast.get('date')}")
    print(f"白天天气: {forecast.get('dayweather')}")
    print(f"白天温度: {forecast.get('daytemp')}°C")
```

### 使用命令行工具

项目提供了一个命令行工具用于测试天气API功能：

```bash
# 运行完整测试
python test_weather.py --test

# 通过城市名称查询天气
python test_weather.py --city 北京

# 通过城市编码查询天气
python test_weather.py --code 110101
```

### 在主应用中查询天气

项目的主应用程序也提供了天气查询功能：

```bash
# 通过城市名称查询天气
python -m src.main --weather-city 上海

# 通过城市编码查询天气
python -m src.main --weather-code 110101
```

### 通过UI交互式查询天气

在UI模式下，可以使用以下命令获取天气信息：

```
查询北京天气
上海天气如何
广州天气预报
天气查询 深圳
```

### 使用LangChain代理查询天气

天气查询工具已与LangChain代理集成，可以通过自然语言进行天气查询：

```python
from src.llm.langchain_agent import run_agent

# 使用LangChain代理查询天气
result = run_agent("查询一下北京的天气情况")
print(result["answer"])

# 查询天气预报
result = run_agent("未来三天上海的天气如何，会下雨吗？")
print(result["answer"])

# 结合业务场景
result = run_agent("根据杭州的天气情况，判断是否需要浇水")
print(result["answer"])
```

## 数据结构说明

### 返回数据结构

天气查询函数返回的数据结构为：

```python
{
    "adcode": "110101",  # 城市编码
    "city": "东城区",     # 城市名称
    "province": "北京市", # 省份名称
    "reporttime": "2023-05-18 09:00:00",  # 天气发布时间
    "timestamp": "2023-05-18T09:05:23.123456",  # 查询时间戳
    
    # 实况天气数据
    "lives": {
        "province": "北京市",
        "city": "东城区",
        "adcode": "110101",
        "weather": "晴",
        "temperature": "25",
        "winddirection": "南",
        "windpower": "≤3",
        "humidity": "40",
        "reporttime": "2023-05-18 08:00:00"
    },
    
    # 天气预报数据（未来3-4天）
    "forecast": [
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
        # 更多天的预报...
    ]
}
```

## LangChain工具集成

天气查询功能已集成到LangChain工具中，以下是相关组件说明：

### WeatherTool类

该工具提供了在LangChain Agent中查询天气的功能：

```python
from src.llm.weather_tools import WeatherTool

# 创建天气查询工具
weather_tool = WeatherTool()

# 执行天气查询
weather_result = weather_tool._run("北京")
print(weather_result)
```

### 在LangChain Agent中使用

系统已自动将WeatherTool注册到LangChain Agent中，可以直接使用：

```python
from src.llm.langchain_agent import run_agent

# LangChain Agent会自动识别天气查询需求并调用相应工具
response = run_agent("北京今天的天气怎么样？温度如何？")
print(response["answer"])
```

## 常见问题

1. **请求天气数据失败**：
   - 检查API密钥是否正确配置
   - 确认网络连接是否正常
   - 检查城市编码是否有效

2. **城市名称无法识别**：
   - 当前版本只支持少量常见城市的名称识别
   - 建议使用城市编码（adcode）来获取更准确的结果

3. **提示"天气API请求失败"**：
   - 检查API访问次数是否达到限额
   - 查看错误码和提示信息，参考[高德API文档](https://lbs.amap.com/api/webservice/guide/tools/info/)

4. **LangChain集成中遇到的问题**：
   - 确保已正确设置OpenAI API密钥
   - 检查LLM Agent是否已正确初始化
   - 检查网络连接以及OpenAI API的可用性

## 城市编码查询

高德地图提供了[城市编码表](https://lbs.amap.com/api/webservice/download)，可以下载获取详细的城市编码列表。

当前系统内置了以下城市的编码：

```markdown
- 北京: 110000
- 上海: 310000
- 广州: 440100
- 深圳: 440300
- 杭州: 330100
- 南京: 320100
- 武汉: 420100
- 成都: 510100
- 重庆: 500000
- 西安: 610100
- 天津: 120000
```

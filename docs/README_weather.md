# SmartIrrigation 天气查询模块

本模块是 SmartIrrigation 智能灌溉系统的组件，提供天气数据查询和处理功能。

## 功能特点

- 基于高德地图天气API，提供准确的天气数据
- 支持通过城市编码或城市名称查询天气
- 获取实时天气和未来3-4天的天气预报
- 数据存储与离线处理支持
- 集成到灌溉决策系统，优化灌溉计划

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置API密钥

在 `config.yaml` 文件中添加高德地图API密钥：

```yaml
apis:
  weather_api_key: "您的高德地图API密钥"
  weather_service_url: "https://restapi.amap.com/v3/weather/weatherInfo"
```

### 运行测试脚本

```bash
# 测试API连接
python test_weather.py --test

# 查询指定城市的天气
python test_weather.py --city 北京

# 通过城市编码查询
python test_weather.py --code 110101
```

## 在项目中使用

```python
from src.data.data_processing import DataProcessingModule

# 初始化数据处理模块
data_processor = DataProcessingModule()

# 获取天气数据
weather = data_processor.get_weather_by_city_name("北京")

# 根据天气数据调整灌溉计划
temperature = float(weather["lives"]["temperature"])
if temperature > 30:
    print("温度较高，增加灌溉量")
elif temperature < 10:
    print("温度较低，减少灌溉量")
```

## 更多信息

详细的API使用说明和数据结构请参考 [天气API使用文档](docs/weather_api_usage.md)。

## 参考资料

- [高德地图开放平台](https://lbs.amap.com/)
- [高德地图天气API文档](https://lbs.amap.com/api/webservice/guide/api/weatherinfo)

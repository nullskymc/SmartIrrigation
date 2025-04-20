# SmartIrrigation
## Task List (开发任务清单)

1.  **环境设置与项目初始化:**
    * [ ] 创建项目结构 (文件夹、虚拟环境)。
    * [ ] 初始化版本控制 (如 Git)。
    * [ ] 安装基础依赖库 (Python, pip)。
2.  **配置管理模块:**
    * [ ] 设计并实现配置加载机制 (如 .env, YAML/JSON 文件)。
    * [ ] 定义配置项 (数据库连接信息, API 密钥, 传感器 ID, 灌溉策略参数, 报警阈值, 日志级别等)。
3.  **数据库模块:**
    * [ ] 选择数据库 (如 PostgreSQL, MySQL) 和 ORM (如 SQLAlchemy) 或数据库驱动。
    * [ ] 定义数据库表模型 (sensor\_data, weather\_data, irrigation\_log, user) - 可放在 `models.py` 或类似文件中。
    * [ ] 实现数据库连接和会话管理。
    * [ ] 实现基础的 CRUD (创建、读取、更新、删除) 操作函数或类。
4.  **异常处理模块:**
    * [ ] 定义自定义异常类 (如 `InvalidSensorData`, `WeatherAPIError`, `LLMCommandError` 等) - 可放在 `exceptions.py` 中。
    * [ ] 配置日志记录器 (使用 `logging` 模块) - 可放在 `logger_config.py` 或 `utils.py` 中。
5.  **数据采集模块 (`data_collection.py`):**
    * [ ] 实现 `DataCollectionModule` 类。
    * [ ] 实现 `__init__` 方法，初始化传感器 ID。
    * [ ] 实现 `get_data` 方法 (模拟或实际读取传感器数据)。
    * [ ] 集成配置模块，读取传感器 ID 和采集频率等设置。
    * [ ] 添加适当的日志记录和异常处理。
6.  **数据处理模块 (`data_processing.py`):**
    * [ ] 实现 `DataProcessingModule` 类。
    * [ ] 实现 `__init__` 方法，初始化天气 API 密钥等配置。
    * [ ] 实现 `process_sensor_data` 方法 (数据清洗、验证)。
    * [ ] 实现 `get_weather_data` 方法 (调用外部天气 API)。
    * [ ] 实现 `process_and_get_weather` 方法 (组合处理流程)。
    * [ ] 集成配置模块读取 API Key。
    * [ ] 添加适当的日志记录和异常处理 (捕获 API 调用错误等)。
7.  **机器学习模型模块 (`ml_model.py`):**
    * [ ] 实现 `SoilMoisturePredictor` 类。
    * [ ] 实现 `__init__` 方法 (模型结构参数)。
    * [ ] 实现 `_initialize_model` (定义 LSTM 或其他模型结构 - 使用 PyTorch 或 TensorFlow/Keras)。
    * [ ] 实现 `_load_pretrained_model` 方法 (加载模型权重)。
    * [ ] 实现 `load_model` 方法 (封装加载逻辑)。
    * [ ] 实现 `_preprocess_data` 方法 (数据归一化等)。
    * [ ] 实现 `predict` 方法 (执行预测)。
    * [ ] (可选) 实现 `train` 方法 (模型训练逻辑)。
    * [ ] 添加适当的日志记录和异常处理 (模型加载失败、预测失败等)。
8.  **LLM 智能体模块 (`llm_agent.py`):**
    * [ ] 实现 `LLMAgentModule` 类。
    * [ ] 实现 `__init__` 方法 (注入 ML 模型实例、灌溉策略)。
    * [ ] 实现 `parse_command` 方法 (解析自然语言指令 - 可能需要集成 NLP 库或调用外部 LLM API)。
    * [ ] 实现 `predict_humidity` 方法 (调用 ML 模型)。
    * [ ] 实现 `make_decision` 方法 (根据策略生成灌溉指令)。
    * [ ] 实现 `generate_alarm` 方法 (生成报警信息)。
    * [ ] 集成配置模块读取灌溉策略。
    * [ ] 添加适当的日志记录和异常处理 (命令解析失败等)。
9.  **控制执行模块 (`control_execution.py`):**
    * [ ] 实现 `ControlExecutionModule` 类。
    * [ ] 实现 `__init__` 方法 (初始化设备状态)。
    * [ ] 实现 `start_irrigation` 方法 (模拟或实际控制硬件)。
    * [ ] 实现 `stop_irrigation` 方法 (模拟或实际控制硬件)。
    * [ ] 实现 `get_status` 方法。
    * [ ] 集成数据库模块记录灌溉日志 (`irrigation_log` 表)。
    * [ ] 添加适当的日志记录和异常处理 (设备控制失败等)。
10. **报警模块 (`alarm.py`):**
    * [ ] 实现 `AlarmModule` 类。
    * [ ] 实现 `__init__` 方法 (初始化报警阈值)。
    * [ ] 实现 `check_humidity` 方法。
    * [ ] 实现 `send_alarm` 方法 (打印、日志记录、或集成外部通知服务如邮件/短信)。
    * [ ] 实现 `handle_alarm` 方法 (组合检查和发送逻辑)。
    * [ ] 实现 `enable_alarm` / `disable_alarm` 方法。
    * [ ] 集成配置模块读取报警阈值。
11. **用户界面模块 (`app.py` 或 `ui.py`):**
    * [ ] 实现 `UserInterfaceModule` 类 (或直接使用函数式方法构建 Gradio 界面)。
    * [ ] 实现 `__init__` (注入 LLM Agent 实例)。
    * [ ] 实现 `handle_user_input` 方法 (调用 LLM Agent 处理输入)。
    * [ ] 实现 `create_ui` 方法 (使用 Gradio 构建界面组件和布局)。
    * [ ] 启动 Gradio 应用。
12. **主程序/服务入口 (`main.py`):**
    * [ ] 实例化各模块。
    * [ ] 处理模块间的依赖注入。
    * [ ] 启动主流程 (例如，启动数据采集定时任务、启动 Gradio 服务)。
13. **安全模块 (`security.py` 或集成到 UI/API 层):**
    * [ ] 实现用户认证逻辑 (JWT)。
    * [ ] 实现密码哈希存储和验证 (bcrypt)。
    * [ ] 实现基于角色的访问控制 (RBAC)。
    * [ ] 实现输入过滤和输出转义 (防 XSS, Prompt 注入)。
    * [ ] 实现 CSRF 防护 (如果需要 Web 表单)。
14. **测试:**
    * [ ] 编写单元测试 (覆盖各模块核心功能)。
    * [ ] 编写集成测试 (测试模块间交互流程)。
    * [ ] (可选) 编写性能测试和压力测试。
15. **文档与部署:**
    * [ ] 完善项目 README。
    * [ ] 编写 API 文档 (如果需要)。
    * [ ] 准备部署脚本或容器化 (Dockerfile)。

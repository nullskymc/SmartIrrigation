from langchain.tools import BaseTool
from sklearn.linear_model import LinearRegression
import numpy as np
from typing import Any, Dict

class SklearnLinearRegressionTool(BaseTool):
    name: str = "sklearn_linear_regression"
    description: str = (
        "使用sklearn线性回归进行简单预测。输入格式：data={'X': [[x1],[x2],...], 'y': [y1,y2,...], 'predict': [[p1],[p2],...]}"
    )

    def _run(self, data: Dict[str, Any] = None) -> Any:
        if not data or not all(k in data for k in ("X", "y", "predict")):
            return "参数data必须包含X, y, predict。"
        try:
            X = np.array(data["X"])
            y = np.array(data["y"])
            predict = np.array(data["predict"])
            model = LinearRegression()
            model.fit(X, y)
            result = model.predict(predict).tolist()
            return result
        except Exception as e:
            return f"线性回归工具异常: {e}"

    async def _arun(self, data: Dict[str, Any] = None) -> Any:
        return self._run(data)

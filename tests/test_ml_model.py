import unittest
from src.ml.ml_model import SoilMoisturePredictor

class TestSoilMoisturePredictor(unittest.TestCase):
    def setUp(self):
        self.model = SoilMoisturePredictor()
    def test_predict(self):
        data = {"data": {"soil_moisture": 40, "temperature": 22, "light_intensity": 500, "rainfall": 0}}
        result = self.model.predict(data)
        self.assertIsInstance(result, float)

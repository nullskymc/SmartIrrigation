import unittest
from src.control.control_execution import ControlExecutionModule

class TestControlExecutionModule(unittest.TestCase):
    def setUp(self):
        self.ctrl = ControlExecutionModule()
    def test_start_stop(self):
        result = self.ctrl.start_irrigation()
        self.assertEqual(result["device_status"], "running")
        result = self.ctrl.stop_irrigation()
        self.assertEqual(result["device_status"], "stopped")
    def test_get_status(self):
        status = self.ctrl.get_status()
        self.assertIn("device_status", status)

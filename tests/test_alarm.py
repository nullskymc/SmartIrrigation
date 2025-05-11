import unittest
from src.alarm.alarm import AlarmModule

class TestAlarmModule(unittest.TestCase):
    def setUp(self):
        self.alarm = AlarmModule(alarm_threshold=30)
    def test_check_humidity(self):
        self.assertTrue(self.alarm.check_humidity(20))
        self.assertFalse(self.alarm.check_humidity(40))
    def test_enable_disable(self):
        self.alarm.disable_alarm()
        self.assertFalse(self.alarm.enabled)
        self.alarm.enable_alarm()
        self.assertTrue(self.alarm.enabled)

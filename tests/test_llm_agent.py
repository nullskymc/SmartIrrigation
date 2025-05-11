import unittest
from src.llm.llm_agent import LLMAgentModule

class TestLLMAgentModule(unittest.TestCase):
    def setUp(self):
        self.agent = LLMAgentModule()
    def test_parse_command(self):
        cmd = "请预测明天湿度"
        result = self.agent.parse_command(cmd)
        self.assertIn("action", result)
    def test_make_decision(self):
        decision = self.agent.make_decision(20)
        self.assertIn("control_command", decision)

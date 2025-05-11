import unittest
from unittest.mock import MagicMock
from src.ui.ui import UserInterfaceModule
from src.llm.llm_agent import LLMAgentModule
from src.control.control_execution import ControlExecutionModule
from src.data.data_collection import DataCollectionModule
from src.data.data_processing import DataProcessingModule

class TestUserInterfaceModule(unittest.TestCase):
    def setUp(self):
        self.ui = UserInterfaceModule(
            llm_agent=LLMAgentModule(),
            control_module=ControlExecutionModule(),
            data_collector=DataCollectionModule(),
            data_processor=DataProcessingModule()
        )
    def test_handle_user_input(self):
        result = self.ui.handle_user_input("预测湿度")
        self.assertIsInstance(result, str)

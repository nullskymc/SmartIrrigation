import unittest
import src.main

class TestMain(unittest.TestCase):
    def test_main_run(self):
        try:
            src.main.main()
        except SystemExit:
            pass  # argparse may call sys.exit()
        except Exception as e:
            self.fail(f"main() raised {e}")

import unittest
from src.security import authenticate, hash_password, check_password

class TestSecurity(unittest.TestCase):
    def test_hash_and_check(self):
        pwd = "test123"
        hashed = hash_password(pwd)
        self.assertTrue(check_password(pwd, hashed))
    def test_authenticate(self):
        token = authenticate("user", "password")
        self.assertIsNotNone(token)

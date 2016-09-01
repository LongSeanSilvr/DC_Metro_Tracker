"""
Unit tests for ___
"""
import unittest
from development_version.src.User import User

# ======================================================================================================================
# Tests
# ======================================================================================================================
class TestCase(unittest.TestCase):

    def test_set_home(self):
        test_user = User("test_user")
        self.assertEqual(test_user.set_home("noma"), "home_updated")

    def test_set_home_invalid(self):
        test_user = User("test_user")
        self.assertEqual(test_user.set_home("the moon"), "invalid_home")

    def test_get_home(self):
        test_user = User("test_user")
        self.assertEqual(test_user.get_home(), "NoMa-Gallaudet U")


# ======================================================================================================================
# Run
# ======================================================================================================================
if __name__ == "__main__":
    unittest.main()
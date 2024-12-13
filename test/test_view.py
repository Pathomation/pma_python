import unittest
from unittest.mock import patch, MagicMock
from pma_python import view


class TestPMAPythonView(unittest.TestCase):

    def setUp(self):
        self.core3 = "https://snapshot.pathomation.com/PMA.core/3.0.3/"

    def test_get_version_info(self):
        version = view.get_version_info(self.core3)
        print(version)
        self.assertIsNotNone(version)

    def test_set_debug_flag(self):
        flag = view.set_debug_flag(flag=False)
        print(flag)
        self.assertIsNone(flag)


if __name__ == "__main__":
    unittest.main()

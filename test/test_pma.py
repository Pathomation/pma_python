import unittest
from pma_python import pma

class TestPMAPythonCore(unittest.TestCase):

    def setUp(self):
        self.test_url = "https://host.pathomation.com/etc/supported_formats.php"

    def test_pma_join(self):
        result = pma._pma_join("https://test.com", "api", "json")
        self.assertEqual(result, "https://test.com/api/json")
        print(result)

    def test_pma_q(self):
        result = pma._pma_q("test string")
        self.assertEqual(result, "test%20string")
        print(result)

    def test_pma_http_get(self):
        url = self.test_url
        headers = {'Accept': 'application/json'}
        response = pma._pma_http_get(url, headers)
        self.assertEqual(response.status_code, 200)
        print(response.text)

    def test_pma_clear_url_cache(self):
        pma._pma_clear_url_cache()
        self.assertEqual(pma._pma_url_content, {})
        print("Cache cleared successfully.")

    def test_pma_set_debug_flag(self):
        pma._pma_set_debug_flag(True)
        self.assertTrue(pma._pma_debug)
        pma._pma_set_debug_flag(False)
        self.assertFalse(pma._pma_debug)
        print("Debug flag toggled successfully.")

    def test_get_supported_formats(self):
        result = pma.get_supported_formats()
        self.assertIsInstance(result, list)
        print(result)

    def test_get_supported_formats_pandas(self):
        result = pma.get_supported_formats(pandas=True)
        try:
            import pandas as pd
            self.assertIsInstance(result, pd.DataFrame)
            print(result.head())
        except ImportError:
            print("Pandas not available, skipping test.")


if __name__ == "__main__":
    unittest.main()

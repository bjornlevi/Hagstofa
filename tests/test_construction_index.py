# tests/test_construction_index.py
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Hagstofan.api_client import APIClient
from Hagstofan.economy.construction_price_index import ConstructionIndex

class TestConstructionIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = APIClient(base_url='https://px.hagstofa.is:443/pxis/api/v1')
        cls.index = ConstructionIndex(cls.client)

    def test_index_is_populated(self):
        self.assertTrue(self.index.index)
        self.assertIsInstance(self.index.index, dict)

    def test_list_categories(self):
        categories = self.index.list_categories()
        self.assertIsInstance(categories, list)
        self.assertGreater(len(categories), 0)

    def test_get_value_for_valid(self):
        category = self.index.list_categories()[0]
        dates = sorted([d for (d, c) in self.index.index if c == category])
        value = self.index.get_value_for(dates[-1], category)
        self.assertIsInstance(value, float)

    def test_get_value_for_invalid(self):
        result = self.index.get_value_for("1990M01", "INVALID")
        self.assertIn("error", result)

    def test_get_historical_values(self):
        category = self.index.list_categories()[0]
        values = self.index.get_historical_values(category, 6)
        self.assertIsInstance(values, list)
        self.assertGreater(len(values), 0)
        for date, val in values:
            self.assertTrue(date.startswith("20"))
            self.assertIsInstance(val, float)

if __name__ == '__main__':
    unittest.main()

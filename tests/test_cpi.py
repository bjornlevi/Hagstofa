import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Hagstofan.api_client import APIClient
from Hagstofan.economy.cpi import CPI
from Hagstofan.economy import isnr_labels

class TestCPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = APIClient(base_url='https://px.hagstofa.is:443/pxis/api/v1')
        cls.cpi = CPI(cls.client)

    def test_index_is_populated(self):
        self.assertTrue(self.cpi.index)
        self.assertIsInstance(self.cpi.index, dict)

    def test_list_is_nr_values_returns_non_empty_list(self):
        is_nr_values = self.cpi.list_is_nr_values()
        self.assertIsInstance(is_nr_values, list)
        self.assertGreater(len(is_nr_values), 0)

    def test_get_value_for_valid_date_is_nr(self):
        is_nr = self.cpi.list_is_nr_values()[0]
        date = max([d for (d, i) in self.cpi.index if i == is_nr])
        value = self.cpi.get_value_for(date, is_nr)
        self.assertIsInstance(value, float)

    def test_get_value_for_invalid_combo(self):
        result = self.cpi.get_value_for("1990M01", "XX")
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)

    def test_get_current_valid_is_nr(self):
        is_nr = self.cpi.list_is_nr_values()[0]
        current = self.cpi.get_current(is_nr)
        self.assertIn("month", current)
        self.assertIn("value", current)

    def test_get_current_invalid_is_nr(self):
        result = self.cpi.get_current("XX")
        self.assertIn("error", result)

    def test_get_12_month_change_valid_is_nr(self):
        is_nr = self.cpi.list_is_nr_values()[0]
        result = self.cpi.get_12_month_change(is_nr)
        if "error" not in result:
            self.assertIn("change_percent", result)
        else:
            self.skipTest("Insufficient data for valid is_nr")

    def test_get_12_month_change_invalid_is_nr(self):
        result = self.cpi.get_12_month_change("XX")
        self.assertIn("error", result)

    def test_iso_labels_format(self):
        for key, label in isnr_labels.ISNRLabels.LABELS.items():
            self.assertIsInstance(key, str)
            self.assertTrue(key.isdigit() or key.startswith("IS"))
            self.assertIsInstance(label, str)
            self.assertGreater(len(label.strip()), 0)

    def test_known_label(self):
        self.assertEqual(isnr_labels.ISNRLabels.get("IS09111"), "Sjónvörp, útvörp og myndspilarar")
        self.assertEqual(isnr_labels.ISNRLabels.get("IS07224"), "Dísel")
        self.assertIsNone(isnr_labels.ISNRLabels.get("EitthvaðRugl"))

    def test_weights_populated(self):
        self.assertTrue(self.cpi.weights)
        self.assertIsInstance(self.cpi.weights, dict)

    def test_weight_for_known_isnr(self):
        if not self.cpi.weights:
            self.skipTest("No weight data available")
        _, known_isnr = next(iter(self.cpi.weights.keys()))
        date = max([d for (d, i) in self.cpi.weights if i == known_isnr])
        value = self.cpi.get_weight(date, known_isnr)
        self.assertIsInstance(value, float)

    def test_weight_for_invalid_combo(self):
        result = self.cpi.get_weight("1990M01", "XX")
        self.assertIsInstance(result, None.__class__)

    def test_increase_over_months_returns_valid_structure(self):
        result = self.cpi.get_increase_over_months(12)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        for isnr, change in result.items():
            self.assertIsInstance(isnr, str)
            self.assertIsInstance(change, float)

    def test_average_and_median_change_valid_isnr(self):
        is_nr = self.cpi.list_is_nr_values()[0]
        result = self.cpi.get_average_and_median_change(is_nr, 12)
        if "error" in result:
            self.skipTest(f"Not enough data for {is_nr}")
        else:
            self.assertIn("average", result)
            self.assertIn("median", result)
            self.assertIsInstance(result["average"], float)
            self.assertIsInstance(result["median"], float)

    def test_average_and_median_change_invalid_isnr(self):
        result = self.cpi.get_average_and_median_change("INVALID", 12)
        self.assertIn("error", result)

    def test_increase_over_months_with_zero_months(self):
        result = self.cpi.get_increase_over_months(0)
        self.assertIsInstance(result, dict)
        self.assertTrue(all(v == 0.0 for v in result.values()))

    def test_increase_over_months_with_large_months(self):
        result = self.cpi.get_increase_over_months(5000)
        self.assertIsInstance(result, dict)
        # It may return fewer entries or 0% for many — just check valid structure
        for k, v in result.items():
            self.assertIsInstance(k, str)
            self.assertIsInstance(v, float)

    def test_average_and_median_change_with_zero_months(self):
        is_nr = self.cpi.list_is_nr_values()[0]
        result = self.cpi.get_average_and_median_change(is_nr, 0)
        self.assertIn("error", result)

    def test_average_and_median_change_with_large_months(self):
        is_nr = self.cpi.list_is_nr_values()[0]
        result = self.cpi.get_average_and_median_change(is_nr, 5000)
        # Accept result with empty or error based on data availability
        if "error" in result:
            self.assertIn("error", result)
        else:
            self.assertIn("average", result)
            self.assertIn("median", result)
            self.assertIsInstance(result["average"], float)
            self.assertIsInstance(result["median"], float)

if __name__ == '__main__':
    unittest.main()

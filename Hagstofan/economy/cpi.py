from Hagstofan.base_data_source import BaseDataSource
from datetime import datetime
from dateutil.relativedelta import relativedelta
from Hagstofan.economy.isnr_labels import ISNRLabels
import re
import statistics

class CPI(BaseDataSource):
    def __init__(self, client):
        super().__init__(client, 'is/Efnahagur/visitolur/1_vnv/2_undirvisitolur/VIS01301.px')

        body = {
            "query": [
                {
                "code": "Liður",
                "selection": {
                    "filter": "item",
                    "values": [
                    "index_B1997"
                    ]
                }
                }
            ],
            "response": {
                "format": "json"
            }
        }
        raw_data = self.get_data(body)

        self.index = {}  # {(date, isnr): value}
        self.isnr_values = set()

        for entry in raw_data.get("data", []):
            key = entry["key"]
            if len(key) < 3:
                continue
            date_str, _, isnr_value = key[0], key[1], key[2]
            if not re.match(r"^IS\d+$", isnr_value):
                continue
            try:
                value = float(entry["values"][0])
            except (ValueError, IndexError):
                continue

            self.index[(date_str, isnr_value)] = value
            self.isnr_values.add(isnr_value)

        # Load weight data from the secondary source
        self.weights = {}  # {(date, isnr): weight}
        weight_source = BaseDataSource(client, 'is/Efnahagur/visitolur/1_vnv/2_undirvisitolur/VIS01305.px')
        weight_body = {
            "query": [],
            "response": {
                "format": "json"
            }
        }
        raw_weights = weight_source.get_data(weight_body)
        for entry in raw_weights.get("data", []):
            key = entry.get("key", [])
            if len(key) < 2:
                continue
            isnr_value, date_str = key[0], key[1]
            if not re.match(r"^IS\d+$", isnr_value):
                continue
            try:
                value = float(entry["values"][0])
            except (ValueError, IndexError):
                continue
            self.weights[(date_str, isnr_value)] = value

    def get_current(self, is_nr: str):
        dates = [d for (d, i) in self.index if i == is_nr]
        if not dates:
            return {"error": f"No data found for ISO '{is_nr}'"}
        latest = max(dates)
        return {"month": latest, "value": self.index.get((latest, is_nr))}

    def get_12_month_change(self, is_nr: str):
        dates = [d for (d, i) in self.index if i == is_nr]
        if not dates:
            return {"error": f"No data found for IS_NR '{is_nr}'"}

        latest_month_str = max(dates)
        try:
            latest_date = datetime.strptime(latest_month_str, "%YM%m")
        except ValueError:
            return {"error": "Invalid date format."}

        previous_date = latest_date - relativedelta(months=12)
        previous_month_str = previous_date.strftime("%YM%m")

        latest_value = self.index.get((latest_month_str, is_nr))
        previous_value = self.index.get((previous_month_str, is_nr))

        if latest_value is None or previous_value is None:
            return {"error": "Insufficient data for 12-month comparison."}

        change = ((latest_value - previous_value) / previous_value) * 100
        return {
            "from": previous_month_str,
            "to": latest_month_str,
            "change_percent": round(change, 2)
        }

    def get_cpi(self):
        return self.get_12_month_change("IS00")

    def list_is_nr_values(self):
        return sorted(self.isnr_values)

    def get_value_for(self, year_month: str, is_nr: str):
        value = self.index.get((year_month, is_nr))
        if value is None:
            return {"error": f"No value found for {year_month} and IS_NR '{is_nr}'"}
        return value

    def get_label_for_is_nr(self, is_nr: str):
        return ISNRLabels.get(is_nr)

    def get_weight(self, year_month: str, is_nr: str):
        """
        Returns the weight of the given ISNR for the specified year and month.

        Args:
            year_month (str): The date in format "YYYYMmm", e.g., "2024M01".
            is_nr (str): The ISNR code, e.g., "IS0112".

        Returns:
            float: The weight value.

        Raises:
            ValueError: If no weight data is found for the specified combination.
        """
        try:
            return self.weights[(year_month, is_nr)]
        except KeyError:
            return None

    def get_increase_over_months(self, n_months: int):
        """
        Calculates the % increase in CPI value over the past n_months for each ISNR.

        Args:
            n_months (int): Number of months back to calculate change from.

        Returns:
            dict: Mapping from ISNR to % change (float), or error message if data is missing.
        """
        result = {}
        for isnr in self.isnr_values:
            dates = [d for (d, i) in self.index if i == isnr]
            if not dates:
                continue

            latest_date_str = max(dates)
            try:
                latest_date = datetime.strptime(latest_date_str, "%YM%m")
            except ValueError:
                continue

            prev_date = latest_date - relativedelta(months=n_months)
            prev_date_str = prev_date.strftime("%YM%m")

            latest_val = self.index.get((latest_date_str, isnr))
            prev_val = self.index.get((prev_date_str, isnr))

            if latest_val is not None and prev_val is not None and prev_val != 0:
                change = ((latest_val - prev_val) / prev_val) * 100
                result[isnr] = round(change, 2)

        return result

    def get_average_and_median_change(self, is_nr: str, n_months: int):
        """
        Computes average and median monthly % change for a given ISNR over the past n_months.

        Args:
            is_nr (str): The ISNR code to compute stats for.
            n_months (int): Number of recent months to include.

        Returns:
            dict: {"average": float, "median": float} or {"error": str}
        """
        dates = sorted([d for (d, i) in self.index if i == is_nr], reverse=True)
        if len(dates) < n_months + 1:
            return {"error": f"Not enough data for ISNR '{is_nr}'"}

        percent_changes = []
        for i in range(n_months):
            d1_str, d2_str = dates[i + 1], dates[i]
            val1 = self.index.get((d1_str, is_nr))
            val2 = self.index.get((d2_str, is_nr))
            if val1 is not None and val2 is not None and val1 != 0:
                pct_change = ((val2 - val1) / val1) * 100
                percent_changes.append(pct_change)

        if not percent_changes:
            return {"error": f"No valid change data for ISNR '{is_nr}'"}

        return {
            "average": round(statistics.mean(percent_changes), 2),
            "median": round(statistics.median(percent_changes), 2)
        }

    def __str__(self):
        total_items = len(self.index)
        unique_isnr = len(self.isnr_values)
        return f"CPI Data Source with {total_items} entries across {unique_isnr} unique ISNR codes."
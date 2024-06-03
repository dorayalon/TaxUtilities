import csv
from datetime import datetime, timedelta
from io import StringIO
from urllib.parse import urlencode

import requests

from config import Config


class BankOfIsraelRates:
    _BASE_URL = "https://edge.boi.gov.il/FusionEdgeServer/sdmx/v2/data/dataflow/BOI.STATISTICS/EXR/1.0/"
    _DATETIME = "Time Period"
    _RATE = "RER_USD_ILS:D:USD:ILS:ILS:OF00"

    @staticmethod
    def _get_params(start_date: str, end_date: str, symbol: str) -> dict:
        """
        :param start_date: A string with the start date in %Y-%m-%d format
        :param end_date: A string with the end date in %Y-%m-%d format
        :param symbol: The symbol
        :return: A dictionary with the URL
        """
        return {
            "c[SERIES_CODE]": f"RER_{symbol}_ILS",
            "format": "csv-series",
            "startperiod": start_date,
            "endperiod": end_date,
        }

    @classmethod
    def _get_url(cls, start_date: str, end_date: str, symbol: str) -> str:
        """
        Get the full URL with the relevant params
        :param start_date: The start date
        :param end_date: The end date
        :param symbol: The symbol
        :return:
        """
        return f"{cls._BASE_URL}?{urlencode(cls._get_params(start_date, end_date, symbol))}"

    @staticmethod
    def _get_dates_list(year: int):
        """
        This method returns a list of all the dates in a given year, with 3 days before the earliest date,
        in case January 1st is a Sunday.
        :param year: The year
        :return: A list of datetime objects
        """
        # Convert the input strings to datetime objects
        start = datetime(year, 1, 1) - timedelta(days=3)  # 3 days in case January 1st is a Sunday
        end = datetime(year, 12, 31)

        date_range = []

        current_date = start
        while current_date <= end:
            date_range.append(current_date.strftime(Config.DATE_FORMAT))
            current_date += timedelta(days=1)

        return date_range

    @classmethod
    def _get_rate_of_date(cls, rates: dict, date: str, end_date: str) -> float:
        """
        This is a recursive method to get the rate for a certain date. If there is no rate existing in the dictionary,
        the rate should be taken from the previous date (again and again recursively, until end_date).
        :param rates: The rates dictionary
        :param date: The date to search for
        :param end_date: The earliest date to search for
        :return:
        """
        if rates.get(date) is not None:
            return rates[date]
        if date < end_date:
            return 0.0
        previous_date = (datetime.strptime(date, Config.DATE_FORMAT) - timedelta(days=1)).strftime(Config.DATE_FORMAT)
        return cls._get_rate_of_date(rates, previous_date, end_date)

    @classmethod
    def get_rates(cls, year: int, symbol: str) -> dict:
        """
        :param year: The year to get the rates for
        :param symbol: The symbol to get the rates for (Usually USD)
        :return: A dictionary with {date: rate} format
        """
        rates = {}
        dates_list = cls._get_dates_list(year)

        url = cls._get_url(dates_list[0], dates_list[-1], symbol)
        response = requests.get(url)
        if response.status_code == 200:
            reader = csv.DictReader(StringIO(response.text))
            for row in reader:
                rates[row[cls._DATETIME]] = float(row[cls._RATE])

        # Add missing dates based on the previous trading day's rate
        for date in dates_list:
            if rates.get(date) is None:
                rates[date] = cls._get_rate_of_date(rates, date, dates_list[0])
        return rates

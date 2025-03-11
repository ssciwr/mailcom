import dateparser
import datefinder
from datetime import datetime


class TimeDetector:
    def __init__(self):
        pass

    def parse_time(self, text: str) -> datetime:
        """Parse the time from text format to datetime format.

        Args:
            text (str): The text to parse the time from.

        Returns:
            datetime: The datetime object of the time parsed.
        """
        return dateparser.parse(text)

    def find_dates(self, text: str) -> list[datetime]:
        """Find dates in a given text.

        Args:
            text (str): The text to find dates in.

        Returns:
            list[str]: A list of dates found in the text.
        """
        return list(datefinder.find_dates(text))

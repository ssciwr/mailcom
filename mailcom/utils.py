import dateparser
import datefinder
from datetime import datetime
import dateparser.search
from mailcom.parse import Pseudonymize


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

    def search_dates(self, text: str, langs=["es", "fr"]) -> list[(str, datetime)]:
        """Search for dates in a given text.

        Args:
            text (str): The text to search for dates in.

        Returns:
            list[(str, datetime)]: A list of tuples containing the date string and the datetime object.
        """
        return dateparser.search.search_dates(text, languages=langs)

    def find_dates(self, text: str) -> list[datetime]:
        """Find dates in a given text.

        Args:
            text (str): The text to find dates in.

        Returns:
            list[datetime]: A list of dates found in the text.
        """
        return list(datefinder.find_dates(text))


if __name__ == "__main__":
    # text = (
    #     "The date in Alice's email is March 19, 2025 at 10:00 AM. "
    #     "She will bring 100$"
    # )
    text = (
        "La date indiquée dans le courriel d'Alice est le 19 mars 2025 à 10 h. "
        "Elle apportera 100 $."
    )
    parse = Pseudonymize()
    parse.init_transformers()
    results = parse.get_ner(text)
    print("transformers")
    for item in results:
        print(item)
    parse.init_spacy("fr")
    doc = parse.nlp_spacy(text)
    print("spacy")
    # does not run as expected
    for token in doc:
        print(token.text, token.pos_)

    time_detector = TimeDetector()
    print(
        "Detected time with datepaser:", time_detector.search_dates(text, langs=["fr"])
    )
    print("Detected time with datefinder:", time_detector.find_dates(text))

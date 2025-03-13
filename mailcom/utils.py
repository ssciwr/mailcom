import dateparser
import datefinder
from datetime import datetime
import dateparser.search
from mailcom.parse import Pseudonymize


class TimeDetector:
    def __init__(self):
        self.parse = Pseudonymize()

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

    def extract_date_time(self, doc: object) -> list:
        """Extract dates from a given text.

        Args:
            doc (object): The spacy doc object.

        Returns:
            list: A list of extracted dates.
        """
        extracted_date_time = []
        for token in doc:
            if token.pos_ in ["NOUN", "NUM", "PROPN", "VERB"]:
                parsed_time = dateparser.parse(token.text)
                if parsed_time:
                    extracted_date_time.append((token, parsed_time))
        return extracted_date_time

    def merge_date_time(
        self, extracted_datetime: list, doc: object
    ) -> list[(str, datetime, int, int)]:
        """Merge the extracted date and time if they are next to each other in the sentence.

        Args:
            extracted_datetime (list): The extracted date and time.
            doc (object): The spacy doc object.

        Returns:
            list[(str, datetime, int, int)]: A list of tuples containing
                the date string, the datetime object, the start index and the end index
        """
        merged_datetime = []
        # if token i and token i+1 are siblings and next to each other,
        # merge them
        count = 0
        for token, parsed_time in extracted_datetime:
            if count < len(extracted_datetime) - 1:
                next_token, next_parsed_time = extracted_datetime[count + 1]
                if (token.nbor() == next_token) and (token.head == next_token.head):
                    new_text = doc[token.i : next_token.i + 1].text
                    new_parsed_time = dateparser.parse(new_text)
                    merged_datetime.append(
                        (
                            new_text,
                            new_parsed_time,
                            token.idx,
                            next_token.idx + len(next_token),
                        )
                    )
                    count += 2
                else:
                    merged_datetime.append(
                        (token.text, parsed_time, token.idx, token.idx + len(token))
                    )
                    count += 1

        return merged_datetime

    def get_date_time(self, text: str, lang="fr") -> list[(str, datetime, int, int)]:
        """Get the date and time from a given text.

        Args:
            text (str): The text to get the date and time from.
            lang (str, optional): The language of the text. Defaults to "fr".

        Returns:
            list[(str, datetime, int, int)]: A list of tuples containing
                the date string, the datetime object, the start index and the end index
        """
        self.parse.init_spacy(lang)
        doc = self.parse.nlp_spacy(text)
        extracted_date_time = self.extract_date_time(doc)
        merged_date_time = self.merge_date_time(extracted_date_time, doc)
        return merged_date_time

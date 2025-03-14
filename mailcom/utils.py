import dateparser
import datefinder
from datetime import datetime
import dateparser.search
from mailcom.parse import Pseudonymize
from spacy.matcher import Matcher
from spacy.tokens import Token
from pandas import Interval


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

    def extract_date_time_multi_words(self, doc: object) -> tuple[list, list]:
        """Extract time from a given text when it is multiple words.
        E.g. 12 mars 2025, 17. April 2024

        Args:
            doc (object): The spacy doc object.

        Returns:
            tuple[list, list]: A list of extracted dates and
                marks of locations in the doc.
        """
        multi_word_date_time = []
        marked_locations = []
        matcher = Matcher(self.parse.nlp_spacy.vocab)
        patterns = [
            [{"POS": "NOUN"}, {"POS": "NOUN"}, {"POS": "NUM"}],
            [
                {"POS": "NUM"},
                {"IS_PUNCT": True, "OP": "?"},
                {},
                {"IS_PUNCT": True, "OP": "?"},
                {"POS": "NUM"},
            ],
            [{"POS": "X"}, {"POS": "X"}, {"POS": "X"}],
            [{"POS": "NOUN"}, {"POS": "NOUN"}],
        ]
        matcher.add("DATE", patterns)
        matches = matcher(doc)
        for _, start, end in matches:
            span = doc[start:end]
            parsed_time = dateparser.parse(span.text)
            if parsed_time:
                multi_word_date_time.append((span, parsed_time))
                marked_locations.append((start, end))
        return multi_word_date_time, marked_locations

    def extract_date_time_single_word(
        self, doc: object, marked_locations: list
    ) -> list:
        """Extract time from a given text when it is only one word.
        E.g. 2009/02/17, 17:23

        Args:
            doc (object): The spacy doc object.
            marked_locations (list): A list of marked locations of dates
                in multiple word format.

        Returns:
            list: A list of extracted dates.
        """
        word_date_time = []
        for token in doc:
            potential_time = token.pos_ in ["NOUN", "NUM", "PROPN", "VERB"] and all(
                (token.i < loc[0] or token.i >= loc[1]) for loc in marked_locations
            )
            if potential_time:
                parsed_time = dateparser.parse(token.text)
                if parsed_time:
                    word_date_time.append((token, parsed_time))
        return word_date_time

    def _get_start_end(self, token_span: object) -> tuple[int, int]:
        """Get the index of a word or span.

        Args:
            token_span (object): The spaCy token or span.

        Returns:
            tuple[int, int]: The start and end index of the word or span.
        """
        if isinstance(token_span, Token):
            return (token_span.i, token_span.i)
        return (
            token_span.start,
            token_span.end - 1,
        )  # the last token also belongs to the span

    def extract_date_time(self, doc: object) -> list:
        """Extract dates from a given text.

        Args:
            doc (object): The spacy doc object.

        Returns:
            list: A list of extracted dates.
        """
        multi_word_date_time, marked_locations = self.extract_date_time_multi_words(doc)
        single_word_date_time = self.extract_date_time_single_word(
            doc, marked_locations
        )
        extracted_date_time = multi_word_date_time + single_word_date_time
        # order the extracted dates
        extracted_date_time.sort(key=lambda x: self._get_start_end(x[0]))
        return extracted_date_time

    def _get_next_sibling(self, token: object) -> object:
        """Get the next sibling of a token.

        Args:
            token (object): The spaCy token.

        Returns:
            object: The next sibling of the token.
        """
        for child in token.head.children:
            if child.i > token.i:
                return child
        return None

    def is_time_mergeable(
        self, first_token: object, second_token: object, doc: object
    ) -> bool:
        """Check if the two time tokens can be merged.
        True: if they are next to each other in the token list,
            or
            the word in between them in ["at", "um", "à", "a las"]
        False: otherwise

        Args:
            first_token (object): The first spaCy token or span.
            second_token (object): The second spaCy token or span.
            doc (object): The spacy doc object.

        Returns:
            bool: True if the tokens can be merged, False otherwise.
        """
        e_first_id = self._get_start_end(first_token)[1]
        s_second_id = self._get_start_end(second_token)[0]
        is_adjacent_words = e_first_id + 1 == s_second_id
        if is_adjacent_words:
            return True

        is_seperated_by_at_punc = (  # e.g. 17. April 2024 at 17:23
            doc[e_first_id + 1].text in ["at", "um", "à", "a las", ","]
            and self._get_start_end(doc[e_first_id + 2])[1] == s_second_id
        )

        if is_seperated_by_at_punc:
            return True

        return False

    def add_merged_datetime(self, merged_datetime: list, new_item: tuple) -> list:
        """Add a new item to the merged datetime list.

        Args:
            merged_datetime (list): The list of merged datetime.
            new_item (tuple): The new item to add.
                It contains the date string, the datetime object,
                the start index and the end index.

        Returns:
            list: The updated list of merged datetime.
        """
        if not merged_datetime:
            merged_datetime.append(new_item)
        else:
            last_item = merged_datetime[-1]
            _, _, last_s_idx, last_e_idx = last_item
            _, _, new_s_idx, new_e_idx = new_item
            last_interval = Interval(last_s_idx, last_e_idx, closed="left")
            new_interval = Interval(new_s_idx, new_e_idx, closed="left")
            if last_interval.overlaps(new_interval):
                # delete the last item and add the new item
                merged_datetime.pop()
                merged_datetime.append(new_item)
            else:
                merged_datetime.append(new_item)
        return merged_datetime

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
        count = 0
        current_pointer, current_parsed_time = extracted_datetime[count]

        while count < len(extracted_datetime) - 1:
            next_pointer, next_parsed_time = extracted_datetime[count + 1]
            if self.is_time_mergeable(current_pointer, next_pointer, doc):
                s_word = self._get_start_end(current_pointer)[0]
                e_word = self._get_start_end(next_pointer)[1]
                s_idx = doc[s_word].idx
                e_idx = doc[e_word].idx + len(doc[e_word])
                new_text = doc[s_word : e_word + 1].text
                new_parsed_time = dateparser.parse(new_text)
                self.add_merged_datetime(
                    merged_datetime,
                    (
                        new_text,
                        new_parsed_time,
                        s_idx,
                        e_idx,
                    ),
                )

                # prepare for the next step
                current_pointer = doc[s_word : e_word + 1]  # a span
                current_parsed_time = new_parsed_time

            else:
                s_word = self._get_start_end(current_pointer)[0]
                e_word = self._get_start_end(current_pointer)[1]
                s_idx = doc[s_word].idx
                e_idx = doc[e_word].idx + len(doc[e_word])
                self.add_merged_datetime(
                    merged_datetime,
                    (
                        current_pointer.text,
                        current_parsed_time,
                        s_idx,
                        e_idx,
                    ),
                )

                # prepare for the next step
                current_pointer = next_pointer
                current_parsed_time = next_parsed_time

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

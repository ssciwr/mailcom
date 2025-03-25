import dateparser
import datefinder
from datetime import datetime
import dateparser.search
from spacy.matcher import Matcher
from spacy.tokens import Token, Doc
from mailcom.utils import SpacyLoader


class TimeDetector:

    def __init__(self, lang, strict_parsing="non-strict"):
        self.lang = lang
        self.spacy_loader = SpacyLoader()
        self.spacy_loader.init_spacy(self.lang)
        self.nlp_spacy = self.spacy_loader.nlp_spacy
        # parse incomplete dates or not
        self.strict_parsing = strict_parsing

        self.patterns = {
            "non-strict": [
                [  # 09 février 2009
                    {"POS": "NOUN", "TEXT": {"NOT_IN": ["-"]}},
                    {"POS": "NOUN", "TEXT": {"NOT_IN": ["-"]}},
                    {"POS": "NUM"},
                ],
                [  # 14 mars 2025 or 17 abr. 2024 or 17. April 2024
                    {"POS": "NUM"},
                    {"IS_PUNCT": True, "OP": "?"},
                    {},
                    {"IS_PUNCT": True, "OP": "?"},
                    {"POS": "NUM"},
                ],
                [{"POS": "X"}, {"POS": "X"}, {"POS": "X"}],  # April 17th 2024
                [  # 2025-03-12
                    {"POS": "NOUN"},
                    {"TEXT": "-"},
                    {"POS": "NOUN"},
                    {"TEXT": "-"},
                    {"POS": "NUM"},
                ],
                [  # 2025-03-01
                    {"POS": "NOUN"},
                    {"TEXT": "-"},
                    {"POS": "NOUN"},
                    {"TEXT": "-"},
                    {"POS": "NOUN"},
                ],
            ]
        }

        # the two below lists need to be updated for each language
        self.time_seps = ["at", "um", "à", ",", ".", "-"]
        self.special_time_seps = [".,", "a las"]
        # SpaCy may not detect numbers as NUM
        # when the language setting differs from the actual language
        self.time_single_word = ["NOUN", "NUM", "PROPN", "VERB", "PRON", "X", "ADV"]

        # special cases for strict parsing
        # 17.04.2024 or 17/04/2024
        self.special_strict_patterns = [
            [
                {
                    "POS": {"IN": self.time_single_word},
                    "TEXT": {"REGEX": r"^\d{1,2}([./])\d{1,2}([./])\d{2,4}"},
                },
            ]
        ]

    def init_strict_patterns(self) -> None:
        """Add strict patterns to the matcher for strict parsing cases."""
        # patterns for the strict parsing cases based on the non-strict ones
        # strict cases: date [] time, e.g. 09 février 2009 17:23
        hour_minutes_patterns = [
            {"OP": "?"},  # separator between date and time is optional
            {
                "POS": {"IN": self.time_single_word},
                "TEXT": {"REGEX": r"^[\d:+.]+$"},  # only numbers, :, +, .
            },
        ]
        strict_patterns = [
            p + hour_minutes_patterns for p in self.patterns["non-strict"]
        ]

        # add the special cases
        for special_pattern in self.special_strict_patterns:
            strict_patterns.append(special_pattern + hour_minutes_patterns)

        self.patterns["strict"] = strict_patterns

    def add_pattern(self, pattern: list[dict], mode: str) -> None:
        """Add a new pattern to the matcher
        if it's a non-empty list of dictionaries and not already present.

        Args:
            pattern (list[dict]): The pattern to add to the matcher.
            mode (str): The mode of the pattern, either "strict" or "non-strict".
        """
        incorrect_format = (
            not pattern
            or not isinstance(pattern, list)
            or not all(isinstance(item, dict) for item in pattern)
        )
        if incorrect_format:
            raise ValueError("Pattern must be a non-empty list of dictionaries.")
        if pattern in self.patterns[mode]:
            raise ValueError("Pattern is already present in the matcher.")
        self.patterns[mode].append(pattern)

    def remove_pattern(self, pattern: list, mode: str) -> None:
        """Remove pattern from the matcher if it's present.

        Args:
            pattern (list): The pattern to remove from the matcher.
            mode (str): The mode of the pattern, either "strict" or "non-strict".
        """
        try:
            self.patterns[mode].remove(pattern)
        except ValueError:
            raise ValueError("Pattern is not present in the matcher.")

    def parse_time(self, text: str) -> datetime:
        """Parse the time from text format to datetime format.

        Args:
            text (str): The text to parse the time from.

        Returns:
            datetime: The datetime object of the time parsed.
        """
        strict = False if self.strict_parsing == "non-strict" else True
        return dateparser.parse(text, settings={"STRICT_PARSING": strict})

    def search_dates(self, text: str, langs=["es", "fr"]) -> list[(str, datetime)]:
        """Search for dates in a given text.

        Args:
            text (str): The text to search for dates in.

        Returns:
            list[(str, datetime)]: A list of tuples containing the date string
                and the datetime object.
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

    def unite_overlapping_words(
        self, multi_word_date_time: list, marked_locations: list, doc: Doc
    ) -> tuple[list, list]:
        """Unite overlapping words between two items in the matched multi-word date time.

        Args:
            multi_word_date_time (list): A list of multi-word date time.
            marked_locations (list): A list of marked locations of dates
                in multiple word format.
            doc (Doc): The spacy doc object.

        Returns:
            tuple[list, list]: A list of updated multi-word date time and
                a list of marked locations.
        """
        updated_multi_word_date_time = []
        updated_marked_locations = []

        if len(multi_word_date_time) <= 1:
            return multi_word_date_time, marked_locations

        count = 0

        while count < len(multi_word_date_time) - 1:
            current_span, _ = multi_word_date_time[count]
            next_span, _ = multi_word_date_time[count + 1]
            if current_span.end >= next_span.start:
                up_s_idx = current_span.start
                up_e_idx = next_span.end
                united_span = doc[up_s_idx:up_e_idx]
                parsed_time = self.parse_time(united_span.text)
                # assuming that the united span is a valid date
                updated_multi_word_date_time.append((united_span, parsed_time))
                updated_marked_locations.append((current_span.start, next_span.end))
                count += 2

            else:
                updated_multi_word_date_time.append(multi_word_date_time[count])
                updated_marked_locations.append(marked_locations[count])
                count += 1

        if count == len(multi_word_date_time) - 1:
            # the last item is not united
            updated_multi_word_date_time.append(multi_word_date_time[-1])
            updated_marked_locations.append(marked_locations[-1])

        return updated_multi_word_date_time, updated_marked_locations

    def extract_date_time_multi_words(self, doc: Doc) -> tuple[list, list]:
        """Extract time from a given text when it is multiple words.
        E.g. 12 mars 2025, 17. April 2024

        Args:
            doc (Doc): The spacy doc object.

        Returns:
            tuple[list, list]: A list of extracted dates and
                marks of locations in the doc.
        """
        # add the strict patterns if needed
        if self.strict_parsing == "strict" and "strict" not in self.patterns:
            self.init_strict_patterns()

        multi_word_date_time = []
        marked_locations = []
        matcher = Matcher(self.nlp_spacy.vocab)
        matcher.add("DATE", self.patterns[self.strict_parsing])
        matches = matcher(doc)
        for _, start, end in matches:
            span = doc[start:end]
            parsed_time = self.parse_time(span.text)
            if parsed_time:
                multi_word_date_time.append((span, parsed_time))
                marked_locations.append((start, end))

        if len(multi_word_date_time) > 1:
            multi_word_date_time, marked_locations = self.unite_overlapping_words(
                multi_word_date_time, marked_locations, doc
            )
        return multi_word_date_time, marked_locations

    def extract_date_time_single_word(self, doc: Doc, marked_locations: list) -> list:
        """Extract time from a given text when it is only one word.
        E.g. 2009/02/17, 17:23

        Args:
            doc (Doc): The spacy doc object.
            marked_locations (list): A list of marked locations of dates
                in multiple word format.

        Returns:
            list: A list of extracted dates.
        """
        word_date_time = []
        for token in doc:
            potential_time = token.pos_ in self.time_single_word and all(
                (token.i < loc[0] or token.i >= loc[1]) for loc in marked_locations
            )
            if potential_time:
                parsed_time = self.parse_time(token.text)
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

    def extract_date_time(self, doc: Doc) -> list:
        """Extract dates from a given text.

        Args:
            doc (Doc): The spacy doc object.

        Returns:
            list: A list of extracted dates.
        """
        multi_word_date_time, marked_locations = self.extract_date_time_multi_words(doc)
        if self.strict_parsing == "non-strict":
            single_word_date_time = self.extract_date_time_single_word(
                doc, marked_locations
            )
        else:
            single_word_date_time = []

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
        self, first_token: object, second_token: object, doc: Doc
    ) -> bool:
        """Check if the two time tokens can be merged.
        True: if they are next to each other in the token list,
            or
            the word in between them in ["at", "um", "à", "a las", ",", ".", "-"],
            or
            the words in between them are [".,"]
        False: otherwise

        Args:
            first_token (object): The first spaCy token or span.
            second_token (object): The second spaCy token or span.
            doc (Doc): The spacy doc object.

        Returns:
            bool: True if the tokens can be merged, False otherwise.
        """
        e_first_id = self._get_start_end(first_token)[1]
        s_second_id = self._get_start_end(second_token)[0]
        is_adjacent_words = e_first_id + 1 == s_second_id
        if is_adjacent_words:
            return True

        is_separated_by_time_seps = (  # e.g. 17. April 2024 at 17:23
            doc[e_first_id + 1].text in self.time_seps
            and self._get_start_end(doc[e_first_id + 2])[0] == s_second_id
        )

        special_time_seps_s_idx = e_first_id + 1
        special_time_seps_e_idx = e_first_id + 3
        is_separated_by_special_time_seps = (  # e.g. mié., 17 abr. 2024
            doc[special_time_seps_s_idx:special_time_seps_e_idx].text
            in self.special_time_seps
            and self._get_start_end(doc[e_first_id + 3])[0] == s_second_id
        )

        if is_separated_by_time_seps or is_separated_by_special_time_seps:
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
            # when the new item contains the last item
            if new_s_idx <= last_s_idx and new_e_idx >= last_e_idx:
                # delete the last item and add the new item
                merged_datetime.pop()
                merged_datetime.append(new_item)
            else:
                merged_datetime.append(new_item)
        return merged_datetime

    def merge_date_time(
        self, extracted_datetime: list, doc: Doc
    ) -> list[(str, datetime, int, int)]:
        """Merge the extracted date and time if they are mergeable.

        Args:
            extracted_datetime (list): The extracted date and time.
            doc (Doc): The spacy doc object.

        Returns:
            list[(str, datetime, int, int)]: A list of tuples containing
                the date string, the datetime object, the start index and the end index
        """
        merged_datetime = []

        if not extracted_datetime:
            return merged_datetime

        if len(extracted_datetime) == 1:
            e_time, e_parsed_time = extracted_datetime[0]
            e_text = e_time.text
            s_word = self._get_start_end(e_time)[0]
            e_word = self._get_start_end(e_time)[1]
            s_idx = doc[s_word].idx
            e_idx = doc[e_word].idx + len(doc[e_word])
            return [
                (
                    e_text,
                    e_parsed_time,
                    s_idx,
                    e_idx,
                )
            ]

        count = 0
        current_pointer, current_parsed_time = extracted_datetime[count]
        merged = False

        while count < len(extracted_datetime) - 1:
            next_pointer, next_parsed_time = extracted_datetime[count + 1]
            s_word = self._get_start_end(current_pointer)[0]
            e_word = self._get_start_end(next_pointer)[1]
            s_idx = doc[s_word].idx
            e_idx = doc[e_word].idx + len(doc[e_word])
            e_new_word = e_word + 1
            new_text = doc[s_word:e_new_word].text
            new_parsed_time = self.parse_time(new_text)
            if (
                self.is_time_mergeable(current_pointer, next_pointer, doc)
                and new_parsed_time
            ):
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
                span_e = e_word + 1
                current_pointer = doc[s_word:span_e]  # a span
                current_parsed_time = new_parsed_time
                merged = True

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
                merged = False

            count += 1

        if not merged:
            # add the last item
            last_item, last_parsed_time = extracted_datetime[count]
            s_word = self._get_start_end(last_item)[0]
            e_word = self._get_start_end(last_item)[1]
            s_idx = doc[s_word].idx
            e_idx = doc[e_word].idx + len(doc[e_word])
            self.add_merged_datetime(
                merged_datetime,
                (
                    last_item.text,
                    last_parsed_time,
                    s_idx,
                    e_idx,
                ),
            )

        return merged_datetime

    def filter_non_numbers(
        self, date_time: list[(str, datetime, int, int)]
    ) -> list[(str, datetime, int, int)]:
        """Filter out the date time phrases that do not contain numbers.

        Args:
            date_time (list[(str, datetime, int, int)]): The original list.

        Returns:
            list[(str, datetime, int, int)]: The filtered list.
        """
        updated_date_time = []
        for dt in date_time:
            words = dt[0].split()
            if any(char.isdigit() for word in words for char in word):
                updated_date_time.append(dt)
        return updated_date_time

    def get_date_time(self, text: str) -> list[(str, datetime, int, int)]:
        """Get the date and time from a given text.

        Args:
            text (str): The text to get the date and time from.
            lang (str, optional): The language of the text. Defaults to "fr".

        Returns:
            list[(str, datetime, int, int)]: A list of tuples containing
                the date string, the datetime object, the start index and the end index
        """
        doc = self.nlp_spacy(text)
        extracted_date_time = self.extract_date_time(doc)
        merged_date_time = self.merge_date_time(extracted_date_time, doc)

        # only keep the date time phrases that contain numbers
        results = self.filter_non_numbers(merged_date_time)
        return results

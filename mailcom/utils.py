import os
from langid.langid import LanguageIdentifier, model
from langdetect import detect_langs, DetectorFactory
from intervaltree import IntervalTree
from transformers import pipeline
from pathlib import Path
from mailcom.inout import InoutHandler
import pandas as pd
import dateparser
import datefinder
from datetime import datetime
import dateparser.search
import spacy as sp
from spacy.matcher import Matcher
from spacy.tokens import Token


def check_dir(path: Path) -> bool:
    """Check if a directory exists at a given path.

    Args:
        path (pathlib.Path)): The path to check.

    Returns:
        bool: True if the directory exists, False otherwise.
    """
    if not os.path.exists(path):
        raise OSError("Path {} does not exist".format(path))
    else:
        return True


def make_dir(path: Path) -> None:
    """Make a directory at a given path.

    Args:
        path (pathlib.Path): The path to make a directory at.
    """
    os.makedirs(path + "/")


def clean_up_content(content: str) -> tuple[str, list]:
    """Clean up the content of an email.

    Args:
        content (str): The content of the email.

    Returns:
        tuple[str, list]: The cleaned up content and a list of cleaned up sentences.
    """
    # remove extra newlines and extra heading and trailing whitespaces
    sentences = content.split("\n")
    updated_sentences = [sent.strip() for sent in sentences if sent.strip()]
    updated_content = "\n".join(updated_sentences)
    return updated_content, updated_sentences


class LangDetector:
    def __init__(self):
        self.lang_id = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        self.detect_langs = detect_langs

    def init_transformers(self, model="papluca/xlm-roberta-base-language-detection"):
        self.lang_detector_trans = pipeline("text-classification", model=model)

    def contains_only_punctuations(self, text: str) -> bool:
        """Check if a given text contains only punctuations.

        Args:
            text (str): The text to check.

        Returns:
            bool: True if the text is only punctuations, False otherwise.
        """
        return not any(char.isalnum() for char in text)

    def strip_punctuations(self, text: str) -> str:
        """Strip punctuations from a given text.

        Args:
            text (str): The text to strip punctuations from.

        Returns:
            str: The text with punctuations stripped.
        """
        return "".join([char for char in text if char.isalnum() or char.isspace()])

    def contains_only_numbers(self, text: str) -> bool:
        """Check if a given text contains only numbers.

        Args:
            text (str): The text to check.

        Returns:
            bool: True if the text is only numbers, False otherwise.
        """
        processed_text = self.strip_punctuations(text)
        processed_text = "".join(
            [char for char in processed_text if not char.isspace()]
        )
        return processed_text.isdigit()

    def contains_only_emails(self, text: str) -> bool:
        """Check if a given text contains only email(s).

        Args:
            text (str): The text to check.

        Returns:
            bool: True if the text contains only email(s), False otherwise.
        """
        processed_text = text.strip().strip("\n")
        text_as_list = [word for word in processed_text.split(" ") if word.strip()]
        return all("@" in word for word in text_as_list)

    def contains_only_links(self, text: str) -> bool:
        """Check if a given text contains only links.

        Args:
            text (str): The text to check.

        Returns:
            bool: True if the text contains only links, False otherwise.
        """
        processed_text = text.strip().strip("\n")
        text_as_list = [word for word in processed_text.split(" ") if word.strip()]
        return all(("http://" in word or ("https://" in word)) for word in text_as_list)

    def constrain_langid(self, lang_set=[]):
        """Set constraint for language set of langid.
        Default is no constrained languages."""
        if lang_set:
            lang_intersec = list(set(lang_set) & set(self.lang_id.nb_classes))
            if lang_intersec:
                self.lang_id.set_languages(lang_intersec)
            else:
                raise ValueError(
                    "No languages in the set are supported by langid. "
                    "Please check the language set."
                )

    def determine_langdetect(self):
        """Enforce consistent results for langdetect."""
        DetectorFactory.seed = 0

    def detect_with_transformers(self, sentence: str) -> list[tuple[str, float]]:
        """Dectect language of a given text using transformers library.

        Args:
            text (str): The text to detect the language of.

        Returns:
            list(str, float): The possible language and their probabilities.
        """
        # checking for attribute first instead of catching exception
        # to avoid repetition of code
        if not hasattr(self, "lang_detector_trans"):
            self.init_transformers()
        detections = self.lang_detector_trans(sentence, top_k=2, truncation=True)
        results = []
        for detection in detections:
            lang = detection["label"]
            prob = detection["score"]
            results.append((lang, prob))
        return results

    def detect_with_langid(self, sentence: str) -> list[tuple[str, float]]:
        """Dectect language of a given text using langid library.
        Recommended for a single language detection.

        Args:
            sentence (str): The text to detect the language of.

        Returns:
            [(str, float)]: The detected language and its probability.
        """
        try:
            lang, prob = self.lang_id.classify(sentence)
        except Exception as e:
            lang = None
            prob = 0.0
            raise ValueError(
                "Error in detecting sentence {}: Error: {}".format(sentence, e)
            )
        return [(lang, prob)]

    def detect_with_langdetect(self, sentence: str) -> list[tuple[str, float]]:
        """Dectect language of a given text using langdetect library.
        Recommended for a single language detection.

        Args:
            text (str): The text to detect the language of.

        Returns:
            list(str, float): The possible language and their probabilities.
        """
        try:
            detections = self.detect_langs(sentence)
            results = [(det.lang, det.prob) for det in detections]
        except Exception as e:
            results = [(None, 0.0)]
            raise ValueError(
                "Error in detecting sentence {}: Error: {}".format(sentence, e)
            )
        return results

    def get_detections(self, text: str, lang_lib="langid") -> list[tuple[str, float]]:
        """Get detections for a given text using a specified lang_lib or model.

        Args:
            text (str): The text to detect the language of.
            lang_lib (str): The lang_lib to use for detection.
                Options are "langid", "langdetect" and "trans".
                The default is "langid".

        Returns:
            list(str, float): A list of detected languages and their probabilities.
        """
        # make sure that the text is not empty,
        # not just whitespace or newline,
        # not only contains punctuations
        if (
            text.strip().strip("\n")
            and not self.contains_only_punctuations(text)
            and not self.contains_only_numbers(text)
            and not self.contains_only_emails(text)
            and not self.contains_only_links(text)
        ):
            if lang_lib == "langid":
                return self.detect_with_langid(text)
            elif lang_lib == "langdetect":
                self.determine_langdetect()
                return self.detect_with_langdetect(text)
            elif lang_lib == "trans":
                return self.detect_with_transformers(text)
            else:
                raise ValueError(
                    "Language library must be either 'langid', 'langdetect' or 'trans'."
                )
        else:
            return [(None, 0.0)]

    def detect_lang_sentences(
        self, sentences: list[str], lang_lib="langid"
    ) -> IntervalTree:
        """Detect languages of a list of sentences using a specified language library.

        Args:
            sentences (str): The document to detect the languages of.
            lang_lib (str): The lang_lib to use for detection.
                Options are "langid", "langdetect" and "trans".

        Returns:
            IntervalTree: An interval tree with the detected languages and their spans.
        """
        result_tree = IntervalTree()
        marked_idx = 0
        current_idx = 0
        current_lang = ""
        for sent in sentences:
            if sent:
                detections = self.get_detections(sent, lang_lib)
                # only take the first detection
                lang, _ = detections[0]
                if lang != current_lang:
                    if current_lang:
                        result_tree.addi(marked_idx, current_idx, current_lang)
                        marked_idx = current_idx
                    current_lang = lang
            current_idx += 1

        result_tree.addi(marked_idx, current_idx, current_lang)
        return result_tree


class SpacyLoader:
    def __init__(self):
        self.spacy_default_model_dict = {
            "es": "es_core_news_md",
            "fr": "fr_core_news_md",
            "de": "de_core_news_md",
            "pt": "pt_core_news_md",
        }

    def init_spacy(self, language: str, model="default"):
        if model == "default":
            # use German as the default language
            model = self.spacy_default_model_dict.get(
                language, self.spacy_default_model_dict["de"]
            )
        try:
            # disable not needed components
            self.nlp_spacy = sp.load(
                model, exclude=["attribute_ruler", "lemmatizer", "ner"]
            )
        except OSError:
            try:
                print(
                    "Could not find model in standard directory. Trying to download model from repo."  # noqa
                )
                # try downloading model
                sp.cli.download(model)
                self.nlp_spacy = sp.load(
                    model,
                    exclude=["attribute_ruler", "lemmatizer", "ner"],
                )
            except SystemExit:
                raise SystemExit("Could not download {} from repo".format(model))


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

    def init_strict_patterns(self) -> None:
        """Add strict patterns to the matcher for strict parsing cases."""
        # patterns for the strict parsing cases based on the non-strict ones
        # strict cases: date [] time, e.g. 09 février 2009 17:23
        possible_time_word = {"POS": {"IN": []}}
        possible_time_word["POS"]["IN"] = self.time_single_word
        hour_minutes_patterns = [
            {"OP": "?"},  # separator between date and time is optional
        ]
        hour_minutes_patterns.append(possible_time_word)
        strict_patterns = [
            p + hour_minutes_patterns for p in self.patterns["non-strict"]
        ]

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

    def unite_overlapping_words(
        self, multi_word_date_time: list, marked_locations: list, doc: object
    ) -> tuple[list, list]:
        """Unite overlapping words between two items in the matched multi-word date time.

        Args:
            multi_word_date_time (list): A list of multi-word date time.
            marked_locations (list): A list of marked locations of dates
                in multiple word format.
            doc (object): The spacy doc object.

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
                united_span = doc[current_span.start : next_span.end]
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

    def extract_date_time_multi_words(self, doc: object) -> tuple[list, list]:
        """Extract time from a given text when it is multiple words.
        E.g. 12 mars 2025, 17. April 2024

        Args:
            doc (object): The spacy doc object.

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

    def extract_date_time(self, doc: object) -> list:
        """Extract dates from a given text.

        Args:
            doc (object): The spacy doc object.

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
        self, first_token: object, second_token: object, doc: object
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
            doc (object): The spacy doc object.

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

        is_separated_by_special_time_seps = (  # e.g. mié., 17 abr. 2024
            doc[e_first_id + 1 : e_first_id + 3].text in self.special_time_seps
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

        while count < len(extracted_datetime) - 1:
            next_pointer, next_parsed_time = extracted_datetime[count + 1]
            s_word = self._get_start_end(current_pointer)[0]
            e_word = self._get_start_end(next_pointer)[1]
            s_idx = doc[s_word].idx
            e_idx = doc[e_word].idx + len(doc[e_word])
            new_text = doc[s_word : e_word + 1].text
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

    def filter_non_numbers(
        self, date_time: list[(str, datetime, int, int)]
    ) -> list[(str, datetime, int, int)]:
        """Filter out the date time phrases that do not contain numbers.

        Args:
            date_time (list[(str, datetime, int, int)]): The list of date and time and their positions.

        Returns:
            list[(str, datetime, int, int)]: The filtered list of date and time and their positions.
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


if __name__ == "__main__":
    # path where the input files can be found
    path_input = Path("./mailcom/test/data_extended/heiBOX/")
    # path where the output files should be written to
    # this is generated if not present yet
    path_output = Path("./data/out/")
    lang_detect_lib = "langid"
    mode = "strict"
    output_filename = "{}_time_detection{}.csv".format(lang_detect_lib, mode)

    # check that input dir is there
    if not check_dir(path_input):
        raise ValueError("Could not find input directory with eml files! Aborting ...")

    # check that the output dir is there, if not generate
    if not check_dir(path_output):
        print("Generating output directory/ies.")
        make_dir(path_output)
    # process the text
    io = InoutHandler(path_input)
    io.list_of_files()
    io.process_emails()

    results = []

    lang_detector = LangDetector()

    for email, path in zip(io.get_email_list(), io.email_path_list):
        if not email["content"]:
            continue
        file_results = {"file": str(path.name)}
        print("Parsing input file {}".format(path.name))
        text, sentences = clean_up_content(email["content"])
        file_results["text"] = text
        file_results["sentences"] = sentences

        # detect language of the email first
        detected_lang = lang_detector.get_detections(text, lang_lib=lang_detect_lib)
        file_results["lang_text"] = "{}-{}".format(
            str(detected_lang[0][0]), str(detected_lang[0][1])
        )

        # detect time based on the language
        time_detector = TimeDetector(detected_lang[0][0], strict_parsing=mode)
        detected_time = time_detector.get_date_time(text)
        detected_time_str = [det[0] for det in detected_time]
        file_results["time_text"] = detected_time_str

        # detect lang and time for each sentence
        lang_tree = lang_detector.detect_lang_sentences(
            sentences, lang_lib=lang_detect_lib
        )

        # for testing only
        # initializing a time detector instance for each sentence is inefficient
        time_sents = []
        for interval in sorted(lang_tree):
            portion_text = "\n".join(sentences[interval.begin : interval.end])
            lang_sent = interval.data
            time_detector = TimeDetector(lang_sent, strict_parsing=mode)
            detected_time_sent = time_detector.get_date_time(portion_text)
            detected_time_sent_str = [det[0] for det in detected_time_sent]
            time_sents.append(
                "{}-{}-{}-{}".format(
                    interval.begin, interval.end, lang_sent, detected_time_sent_str
                )
            )
        file_results["time_sents"] = time_sents

        results.append(file_results)

    # write results to file
    df = pd.DataFrame(results)
    df.to_csv(path_output / output_filename, index=False)

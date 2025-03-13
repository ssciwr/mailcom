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


if __name__ == "__main__":
    # path where the input files can be found
    path_input = Path("./mailcom/test/data_extended/heiBOX/")
    # path where the output files should be written to
    # this is generated if not present yet
    path_output = Path("./data/out/")
    output_filename = "lang_detection.csv"

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

    for email, path in zip(io.get_email_list(), io.email_path_list):
        if not email["content"]:
            continue
        file_results = {"file": str(path.name)}
        print("Parsing input file {}".format(path.name))
        text = email["content"]

        # Test functionality of LangDetector class in utils.py
        lang_detector = LangDetector()
        lang_detector.init_transformers()
        sentences = text.split("\n")
        for lang_lib in ["langid", "langdetect", "trans"]:
            detected_lang = lang_detector.get_detections(text, lang_lib)
            lang_tree = lang_detector.detect_lang_sentences(sentences, lang_lib)
            file_results[lang_lib + "_text"] = "{}-{}".format(
                str(detected_lang[0][0]), str(detected_lang[0][1])
            )
            file_results[lang_lib + "_sentence"] = str(lang_tree)

        results.append(file_results)

    # write results to file
    df = pd.DataFrame(results)
    df_reordered = df.iloc[:, [0, 1, 3, 5, 2, 4, 6]]
    df_reordered.to_csv(path_output / output_filename, index=False)

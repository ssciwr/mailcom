from langid.langid import LanguageIdentifier, model
from langdetect import detect_langs, DetectorFactory
from intervaltree import IntervalTree
from transformers import pipeline


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

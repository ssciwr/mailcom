import os
from langid.langid import LanguageIdentifier, model
from langdetect import detect_langs, DetectorFactory
from intervaltree import IntervalTree


def check_dir(path: str) -> bool:
    if not os.path.exists(path):
        raise OSError("Path {} does not exist".format(path))
    else:
        return True


def make_dir(path: str):
    # make directory at path
    os.makedirs(path + "/")


class LangDetector:
    def __init__(self):
        self.lang_id = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        self.detect_langs = detect_langs

    def constrain_langid(self, lang_set=[]):
        """Set constraint for language set of langid. Default is no constrained languages.
        """
        if lang_set:
            lang_intersec = list(set(lang_set) & set(self.lang_id.nb_classes))
            if lang_intersec:
                self.lang_id.set_languages(lang_intersec)
            else:
                raise ValueError(
                    "No languages in the set are supported by langid. Please check the language set."
                )
    
    def determine_langdetect(self):
        """Enforce consistent results for langdetect.
        """
        DetectorFactory.seed = 0

    def detect_with_langid(self, sentence: str) -> list[tuple[str, float]]:
        """Dectect language of a given text using langid library.
        Recommended for a single language detection.

        Args:
            sentence (str): The text to detect the language of.

        Returns:
            [(str, float)]: The detected language and its probability.
        """
        lang, prob = self.lang_id.classify(sentence)
        return [(lang, prob)]
    
    def detect_with_langdetect(self, sentence: str) -> list[tuple[str, float]]:
        """Dectect language of a given text using langdetect library.
        Recommended for a single language detection.

        Args:
            text (str): The text to detect the language of.

        Returns:
            list(str, float): The possible language and their probabilities.
        """
        detections = self.detect_langs(sentence)
        results = [(det.lang, det.prob) for det in detections]
        return results
    
    def get_detections(self, text: str, lang_lib="langdetect") -> list[tuple[str, float]]:
        """Get detections for a given text using a specified lang_lib.

        Args:
            text (str): The text to detect the language of.
            lang_lib (str): The lang_lib to use for detection. Options are "langid" and "langdetect".

        Returns:
            list(str, float): A list of detected languages and their probabilities.
        """
        if lang_lib == "langid":
            return self.detect_with_langid(text)
        elif lang_lib == "langdetect":
            self.determine_langdetect()
            return self.detect_with_langdetect(text)
        else:
            raise ValueError("Language library must be either 'langid' or 'langdetect'.")
        
    def detect_lang_sentences(self, sentences: list[str], lang_lib="langdetect") -> IntervalTree:
        """Detect languages of a list of sentences using a specified language library.

        Args:
            sentences (str): The document to detect the languages of.
            lang_lib (str): The lang_lib to use for detection. Options are "langid" and "langdetect".

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
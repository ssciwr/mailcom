import os
from langid.langid import LanguageIdentifier, model
from langdetect import detect_langs, DetectorFactory


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

    def detect_with_langid(self, text: str):
        """Dectect language of a given text using langid library.

        Args:
            text (str): The text to detect the language of.

        Returns:
            [(str, float)]: The detected language and its probability.
        """
        lang, prob = self.lang_id.classify(text)
        return [(lang, prob)]
    
    def detect_with_langdetect(self, text: str):
        """Dectect language of a given text using langdetect library.

        Args:
            text (str): The text to detect the language of.

        Returns:
            list(str, float): The possible language and their probabilities.
        """
        detections = self.detect_langs(text)
        results = [(det.lang, det.prob) for det in detections]
        return results
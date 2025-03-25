import os
from pathlib import Path
import spacy as sp
from transformers import pipeline


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


class SpacyLoader:
    def __init__(self):
        self.spacy_default_model = {
            "es": "es_core_news_md",
            "fr": "fr_core_news_md",
            "de": "de_core_news_md",
            "pt": "pt_core_news_md",
        }

    def init_spacy(self, language: str, model="default"):
        if model == "default":
            # use German as the default language
            model = self.spacy_default_model.get(
                language, self.spacy_default_model["de"]
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


class TransformerLoader:
    def __init__(self):
        self.trans_default_model = {
            "ner": {
                "task": "token-classification",
                "model": "xlm-roberta-large-finetuned-conll03-english",
                "revision": "18f95e9",
                "aggregation_strategy": "simple",
            },
            "lang_detector": {
                "task": "text-classification",
                "model": "papluca/xlm-roberta-base-language-detection",
            },
        }

        self.trans_instances = {}

    def init_transformers(self, feature: str):
        setting_info = self.trans_default_model.get(feature)
        if not setting_info:
            raise ValueError("Invalid feature: {}".format(feature))

        self.trans_instances[feature] = pipeline(**setting_info)

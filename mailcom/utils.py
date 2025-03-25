import os
from pathlib import Path
import spacy as sp


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

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
            "en": "en_core_web_md",
        }

        self.spacy_instances = {}

    def get_default_model(self, language: str):
        # special case for Galician
        if language == "gl":
            return "pt", self.spacy_default_model["pt"]
        # use German as the default language
        if language not in self.spacy_default_model:
            return "de", self.spacy_default_model["de"]
        return language, self.spacy_default_model[language]

    def init_spacy(self, language: str, model="default"):
        if model == "default":
            language, model = self.get_default_model(language)
        if language not in self.spacy_instances:
            self.spacy_instances[language] = {}

        try:
            # disable not needed components
            self.spacy_instances[language][model] = sp.load(
                model, exclude=["lemmatizer", "ner"]
            )
        except OSError:
            try:
                print(
                    "Could not find model in standard directory. Trying to download model from repo."  # noqa
                )
                # try downloading model
                sp.cli.download(model)
                self.spacy_instances[language][model] = sp.load(
                    model,
                    exclude=["lemmatizer", "ner"],
                )
            except SystemExit:
                raise SystemExit("Could not download {} from repo".format(model))


def get_spacy_instance(
    spacy_loader: SpacyLoader, language: str, model: str = "default"
):
    """Get the spacy instance for a given language and model.

    Args:
        spacy_loader (SpacyLoader): The spacy loader.
        language (str): The language of the spacy instance.
        model (str): The model of the spacy instance, defaults to "default".

    Returns:
        spacy.Language: The spacy instance.
    """
    if spacy_loader is None:
        raise ValueError("Spacy loader is not provided.")

    if model == "default":
        language, model = spacy_loader.get_default_model(language)

    if (
        language not in spacy_loader.spacy_instances
        or model not in spacy_loader.spacy_instances[language]
    ):
        # init the spacy instance
        spacy_loader.init_spacy(language, model)

    return spacy_loader.spacy_instances[language][model]


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

    def init_transformers(self, feature: str, pipeline_info: dict = None):
        if not pipeline_info:
            pipeline_info = self.trans_default_model.get(feature)
        if not pipeline_info:
            raise ValueError("Invalid feature: {}".format(feature))

        try:
            self.trans_instances[feature] = pipeline(**pipeline_info)
        except TypeError:
            raise TypeError(
                "Incorrect format of pipeline_info: {}".format(pipeline_info)
            )
        except RuntimeError as e:
            raise RuntimeError("Could not load transformer: {}".format(e))
        except KeyError as e:
            raise KeyError("Invalid pipeline_info key: {}".format(e))


def get_trans_instance(
    trans_loader: TransformerLoader, feature: str, pipeline_info: dict = None
):
    """Get the transformer instance for a given feature.

    Args:
        trans_loader (TransformerLoader): The transformer loader.
        feature (str): The feature to get the transformer instance.
        pipeline_info (dict): The setting info for the transformer, defaults to None.

    Returns:
        pipeline: The transformer instance.
    """
    if trans_loader is None:
        raise ValueError("Transformer loader is not provided.")

    if feature not in trans_loader.trans_instances:
        # init the transformer pipeline
        trans_loader.init_transformers(feature, pipeline_info)

    return trans_loader.trans_instances[feature]

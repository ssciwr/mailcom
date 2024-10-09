import os
import spacy as sp
from transformers import pipeline
from pathlib import Path
from mailcom.inout import InoutHandler

# please modify this section depending on your setup
# input language - either "es" or "fr"
# will also need pt
lang = "es"
# lang = "fr"
# path where the input files can be found
path_input = Path("./test/data/")
# path where the output files should be written to
# this is generated if not present yet
path_output = Path("../data/out/")
# the ner tool - currently only "transformers"
tool = "transformers"
# please do not modify below this section unless you know what you are doing


class Pseudonymize:
    def __init__(self):

        self.spacy_default_model_dict = {
            "es": "es_core_news_md",
            "fr": "fr_core_news_md",
        }

        self.pseudo_first_names = {
            "es": [
                "ES_FIRST_NAME_1",
                "ES_FIRST_NAME_2",
                "ES_FIRST_NAME_3",
                "ES_FIRST_NAME_4",
            ],
            "fr": [
                "FR_FIRST_NAME_1",
                "FR_FIRST_NAME_2",
                "FR_FIRST_NAME_3",
                "FR_FIRST_NAME_4",
            ],
        }

        self.pseudo_last_names = {
            "es": [
                "ES_LAST_NAME_1",
                "ES_LAST_NAME_2",
                "ES_LAST_NAME_3",
                "ES_LAST_NAME_4",
            ],
            "fr": [
                "FR_LAST_NAME_1",
                "FR_LAST_NAME_2",
                "FR_LAST_NAME_3",
                "FR_LAST_NAME_4",
            ],
        }

    def init_spacy(self, language: str, model="default"):
        if model == "default":
            model = self.spacy_default_model_dict[language]
        try:
            # disable not needed components
            self.nlp_spacy = sp.load(
                model, exclude=["morphologizer", "attribute_ruler", "lemmatizer", "ner"]
            )
        except OSError:
            raise OSError("Could not find {} in standard directory.".format(model))

        self.nlp_spacy = sp.load(model)

    def init_transformers(self, model="default", model_revision_number="default"):
        if model == "default":
            model = "xlm-roberta-large-finetuned-conll03-english"
        # TODO: Model revision number

        # ner_recognizer = pipeline("token-classification")
        self.ner_recognizer = pipeline("token-classification", model=model)

    def get_sentences(self, input_text):
        doc = self.nlp_spacy(input_text)
        text_as_sents = []
        for sent in doc.sents:
            text_as_sents.append(str(sent))
        return text_as_sents

    def get_ner(self, sentence):
        ner = self.ner_recognizer(sentence)
        return ner

    def pseudonymize_sentence(self, ner, sentence):
        # remove any named entities
        if ner:
            # found named entities
            entlist = []
            new_sentence = sentence
            additional_sentence_length = 0
            for i in range(len(ner)):
                entity = ner[i]
                # check whether this entity has already been processed
                # because it is part of a previous word
                if entity.get("replaced", False):
                    continue
                entity["replaced"] = True
                ent_string = entity["entity"]  # noqa
                # here we could check that string is "I-PER"
                ent_conf = entity["score"]  # noqa
                ent_position = entity["start"], entity["end"]
                print(entity)
                # Here we have to be careful - tokenization with
                # transformers is quite different from spacy/stanza/flair
                # here we get character ids
                entlist.append(ent_position)
                # now replace respective characters
                # replace I-PER
                if ent_string == "I-PER":
                    # add all following entities to this name
                    j = i
                    word_end = entity["end"]
                    if j < len(ner) - 1:
                        while ner[j]["end"] == ner[j + 1]["start"]:
                            ner[j + 1]["replaced"] = True
                            word_end = ner[j + 1]["end"]
                            j += 1
                            if j == len(ner) - 1:
                                break
                    # replace the entire name
                    # if there is another entity before this name with one char inbetween,
                    # this is likely a last name
                    # TODO: get the language information
                    if i > 0 and entity["start"] - ner[i - 1]["end"] == 1:
                        pseudonym = self.pseudo_last_names["fr"][0]
                    else:
                        pseudonym = self.pseudo_first_names["fr"][0]
                    new_sentence = (
                        new_sentence[: ent_position[0] + additional_sentence_length]
                        + pseudonym
                        + new_sentence[
                            (word_end + additional_sentence_length) :  # noqa
                        ]
                    )
                    # since the position of chars in the sentence now changes,
                    # record the additional sentence length
                    additional_sentence_length += len(pseudonym) - (
                        word_end - ent_position[0]
                    )
                else:
                    new_sentence = (
                        new_sentence[: (ent_position[0] + additional_sentence_length)]
                        + "x" * (ent_position[1] - ent_position[0])
                        + new_sentence[
                            (ent_position[1] + additional_sentence_length) :  # noqa
                        ]
                    )
            newlist = [new_sentence]
        else:
            # no named entities found
            newlist = [sentence]
        return newlist

    def concatenate(self, sentences):
        return " ".join(sentences)

    def pseudonymize(self, text: str):
        sentences = self.get_sentences(text)
        pseudonymized_sentences = []
        for sent in sentences:
            ner = self.get_ner(sent)
            ps_sent = self.pseudonymize_sentence(ner, sent)
            pseudonymized_sentences.append(" ".join(ps_sent))
        return self.concatenate(pseudonymized_sentences)


def get_sentences(doc):
    # spacy
    text = []
    for sent in doc.sents:
        text.append(str(sent))
    return text


def process_doc(doc, ner_tool="transformers", text=None):
    # remove any named entities
    if ner_tool == "transformers":
        if doc:
            # found named entities
            entlist = []
            newtext = text
            for entity in doc:
                ent_string = entity["entity"]  # noqa
                # here we could check that string is "I-PER"
                ent_conf = entity["score"]  # noqa
                ent_position = entity["start"], entity["end"]
                # Here we have to be careful - tokenization with
                # transformers is quite different from spacy/stanza/flair
                # here we get character ids
                entlist.append(ent_position)
                # now replace respective characters
                newtext = (
                    newtext[: ent_position[0]]
                    + "x" * (ent_position[1] - ent_position[0])
                    + newtext[ent_position[1] :]  # noqa
                )
            newlist = [newtext]
        else:
            # no named entities found
            newlist = [text]
    return newlist


def init_spacy(lang):
    # the md models seem most accurate
    if lang == "es":
        # model = "es_core_news_sm"
        model = "es_core_news_md"
        # model = "es_core_news_lg"
        # model = "es_dep_news_trf"
    elif lang == "fr":
        # model = "fr_core_news_sm"
        model = "fr_core_news_md"
        # model = "fr_core_news_lg"
        # model = "fr_dep_news_trf"
    else:
        print("model not found, aborting")
        exit()
    # initialize nlp pipeline
    try:
        # disable not needed components
        nlp = sp.load(
            model, exclude=["morphologizer", "attribute_ruler", "lemmatizer", "ner"]
        )
    except OSError:
        raise OSError("Could not find {} in standard directory.".format(model))
    nlp = sp.load(model)
    return nlp


def init_transformers():
    # ner_recognizer = pipeline("token-classification")
    ner_recognizer = pipeline(
        "token-classification", model="xlm-roberta-large-finetuned-conll03-english"
    )
    return ner_recognizer


def check_dir(path: str) -> bool:
    if not os.path.exists(path):
        raise OSError("Path {} does not exist".format(path))
    else:
        return True


def make_dir(path: str):
    # make directory at path
    os.makedirs(path + "/")


if __name__ == "__main__":
    # nlp_spacy = init_spacy(lang)
    # nlp_transformers = init_transformers()

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
    # html_files = list_of_files(path_input, "html")
    pseudonymizer = Pseudonymize()
    pseudonymizer.init_spacy("fr")
    pseudonymizer.init_transformers()
    for file in io.email_list:
        text = io.get_text(file)
        text = io.get_html_text(text)
        # print(text)
        # print(io.email_content["date"])
        # print(io.email_content["attachment"])
        # print(io.email_content["attachement type"])
        # skip this text if email could not be parsed
        if not text:
            continue
        # doc_spacy = nlp_spacy(text)
        # text = get_sentences(doc_spacy)
        # start with first line
        # here you can limit the number of sentences to parse
        # newlist = []
        # max_i = len(text)
        # for i in range(0, max_i):
        #     if tool == "transformers":
        #         nlps = nlp_transformers(text[i])
        #         doc = nlps
        #     newlist.append(process_doc(doc, ner_tool=tool, text=text[i]))
        #     newlist[i] = " ".join(newlist[i])
        # join the new and old lines for comparison
        # printout = "New: " + " ".join(newlist) + "\n"
        # printout = printout + "Old: " + " ".join(text[0:max_i])
        # write_file(printout, path_output + "/" + file)

        # Test functionality of Pseudonymize class
        output_text = pseudonymizer.pseudonymize(text)
        print("New text:", output_text)
        print("Old text:", text)

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
path_input = Path("./mailcom/test/data/")
# path where the output files should be written to
# this is generated if not present yet
path_output = Path("./data/out/")
output_filename = "dict"
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
                "José",
                "Angel",
                "Alex",
                "Ariel",
                "Cruz",
                "Fran",
                "Arlo",
                "Adri",
                "Marce",
                "Mati",
            ],
            "fr": [
                "Claude",
                "Dominique",
                "Claude",
                "Camille",
                "Charlie",
                "Florence",
                "Francis",
                "Maxime",
                "Remy",
                "Cécile",
            ],
        }

        # records the already replaced names in an email
        self.used_first_names = {}

    def init_spacy(self, language: str, model="default"):
        if model == "default":
            model = self.spacy_default_model_dict[language]
        try:
            # disable not needed components
            self.nlp_spacy = sp.load(
                model, exclude=["morphologizer", "attribute_ruler", "lemmatizer", "ner"]
            )
        except OSError:
            pass
        try:
            print(
                "Could not find model in standard directory. Trying to download model from repo."  # noqa
            )
            # try downloading model
            sp.cli.download(model)
            self.nlp_spacy = sp.load(
                model,
                exclude=["morphologizer", "attribute_ruler", "lemmatizer", "ner"],
            )
        except SystemExit:
            raise SystemExit("Could not download {} from repo".format(model))
        except OSError:
            raise OSError("Could not find {} in standard directory".format(model))

    def init_transformers(
        self,
        model="xlm-roberta-large-finetuned-conll03-english",
        model_revision_number="18f95e9",
    ):
        self.ner_recognizer = pipeline(
            "token-classification",
            model=model,
            revision=model_revision_number,
            aggregation_strategy="simple",
        )

    def reset(self):
        # reset used names for processing a new email
        self.used_first_names.clear()

    def get_sentences(self, input_text):
        doc = self.nlp_spacy(input_text)
        text_as_sents = []
        for sent in doc.sents:
            text_as_sents.append(str(sent))
        return text_as_sents

    def get_ner(self, sentence):
        ner = self.ner_recognizer(sentence)
        return ner

    def pseudonymize_per(self, new_sentence, nelist):
        unique_ne_list = list(dict.fromkeys(nelist))
        for ne in unique_ne_list:
            # choose the pseudonym
            nm_list = self.used_first_names
            pseudo_list = self.pseudo_first_names
            pseudonym = ""
            name_variations = [
                ne,
                ne.lower(),
                ne.title(),
            ]
            # if this name has been replaced before, choose the same pseudonym
            for nm_var in name_variations:
                pseudonym = nm_list.get(nm_var, "")
                if pseudonym != "":
                    break
            # if none is found, choose a new pseudonym
            if pseudonym == "":
                try:
                    pseudonym = pseudo_list["fr"][
                        len(nm_list)
                    ]  # reaches end of the list
                except IndexError:
                    pseudonym = pseudo_list["fr"][0]
                nm_list[ne] = pseudonym
            # replace all occurences with pseudonym
            new_sentence = new_sentence.replace(ne, pseudonym)
        return new_sentence

    def pseudonymize_ne(self, ner, sentence):
        # remove any named entities
        entlist = []
        nelist = []
        new_sentence = sentence
        for i in range(len(ner)):
            entity = ner[i]
            ent_string = entity["entity_group"]  # noqa
            # here we could check that string is "PER"
            ent_conf = entity["score"]  # noqa
            ent_position = entity["start"], entity["end"]
            # Here we have to be careful - tokenization with
            # transformers is quite different from spacy/stanza/flair
            # here we get character ids
            entlist.append(ent_position)
            # now replace respective characters
            # replace PER
            if ent_string == "PER":
                # add the name of this entity to list
                nelist.append(entity["word"])
            else:
                # Locations and Organizations
                new_sentence = (
                    new_sentence[: (ent_position[0])]
                    + "x" * (ent_position[1] - ent_position[0])
                    + new_sentence[(ent_position[1]) :]  # noqa
                )
        # replace all unique PER now
        new_sentence = self.pseudonymize_per(new_sentence, nelist)

        newlist = [new_sentence]
        return newlist

    def pseudonymize_numbers(self, sentence):
        sent_as_list = list(sentence)
        sent_as_list = [char if not char.isdigit() else "x" for char in sent_as_list]
        return "".join(sent_as_list)

    def concatenate(self, sentences):
        return " ".join(sentences)

    def pseudonymize(self, text: str):
        self.reset()
        sentences = self.get_sentences(text)
        pseudonymized_sentences = []
        for sent in sentences:
            ner = self.get_ner(sent)
            ps_sent = " ".join(self.pseudonymize_ne(ner, sent)) if ner else sent
            ps_sent = self.pseudonymize_numbers(ps_sent)
            pseudonymized_sentences.append(ps_sent)
        return self.concatenate(pseudonymized_sentences)


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
        print("Parsing input file {}".format(file))
        text = io.get_text(file)
        text = io.get_html_text(text)
        xml = io.data_to_xml(text)
        io.write_file(xml, path_output / output_filename)
        if not text:
            continue
        # Test functionality of Pseudonymize class
        output_text = pseudonymizer.pseudonymize(text)
        print("New text:", output_text)
        print("Old text:", text)

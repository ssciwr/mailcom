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
        # amount of sentences passed to transformers ner_classification
        # -1 corresponds to all sentences
        self.n_batch_sentences = 1

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

        # records NEs in the last email
        self.per_list = []
        self.org_list = []
        self.loc_list = []
        self.misc_list = []

    def set_sentence_batch_size(self, batch_size: int):
        if batch_size == 0 or batch_size < -1:
            raise ValueError(
                "Batch size should either be a positive integer or -1 for all sentences."
            )
        self.n_batch_sentences = batch_size

    def init_spacy(self, language: str, model="default"):
        if model == "default":
            model = self.spacy_default_model_dict[language]
        try:
            # disable not needed components
            self.nlp_spacy = sp.load(
                model, exclude=["morphologizer", "attribute_ruler", "lemmatizer", "ner"]
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
                    exclude=["morphologizer", "attribute_ruler", "lemmatizer", "ner"],
                )
            except SystemExit:
                raise SystemExit("Could not download {} from repo".format(model))

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
        # reset NEs
        self.per_list.clear()
        self.org_list.clear()
        self.loc_list.clear()
        self.misc_list.clear()

    def get_sentences(self, input_text):
        doc = self.nlp_spacy(input_text)
        text_as_sents = []
        for sent in doc.sents:
            text_as_sents.append(str(sent))
        return text_as_sents

    def get_ner(self, sentence):
        ner = self.ner_recognizer(sentence)
        return ner

    def pseudonymize_per(self, new_sentence):
        unique_ne_list = list(dict.fromkeys(self.per_list))
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
        new_sentence = sentence
        for i in range(len(ner)):
            entity = ner[i]
            ent_string = entity["entity_group"]  # noqa
            ent_word = entity["word"]
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
                self.per_list.append(ent_word)
            # replace LOC
            elif ent_string == "LOC":
                new_sentence = new_sentence.replace(ent_word, "[location]")
                self.loc_list.append(ent_word)
            # replace ORG
            elif ent_string == "ORG":
                new_sentence = new_sentence.replace(ent_word, "[organization]")
                self.org_list.append(ent_word)
            # replace MISC
            elif ent_string == "MISC":
                new_sentence = new_sentence.replace(ent_word, "[misc]")
                self.misc_list.append(ent_word)
        # replace all unique PER now
        new_sentence = self.pseudonymize_per(new_sentence)

        newlist = [new_sentence]
        return newlist

    def pseudonymize_numbers(self, sentence):
        sent_as_list = list(sentence)
        new_list = []
        for i in range(len(sent_as_list)):
            if sent_as_list[i].isdigit():
                if i == 0 or not sent_as_list[i - 1].isdigit():
                    new_list.append("[number]")
            else:
                new_list.append(sent_as_list[i])

        return "".join(new_list)

    def pseudonymize_email_addresses(self, sentence):
        split = sentence.split(" ")
        new_list = []
        for word in split:
            if "@" in word:
                new_list.append("[email]")
            else:
                new_list.append(word)
        return " ".join(new_list)

    def concatenate(self, sentences):
        return " ".join(sentences)

    def pseudonymize(self, text: str):
        self.reset()
        sentences = self.get_sentences(text)
        batches = [
            sentences[n : n + self.n_batch_sentences]  # noqa
            for n in range(0, len(sentences), self.n_batch_sentences)
        ]
        pseudonymized_batches = []
        for batch in batches:
            batch = self.concatenate(batch)
            batch = self.pseudonymize_email_addresses(batch)
            ner = self.get_ner(batch)
            ps_sent = " ".join(self.pseudonymize_ne(ner, batch)) if ner else batch
            ps_sent = self.pseudonymize_numbers(ps_sent)
            pseudonymized_batches.append(ps_sent)
        return self.concatenate(pseudonymized_batches)


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
    pseudonymizer.set_sentence_batch_size(2)
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

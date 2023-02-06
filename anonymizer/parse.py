import os
import spacy as sp
import stanza as sa
# from flair.data import Sentence
# from flair.models import SequenceTagger
from transformers import pipeline
import in_out as in_out

# please modify this section depending on your setup
# input language - either "es" or "fr"
lang = "es"
# lang = "fr"
# path where the input files can be found
path_input = "./data/SGsp/"
# path where the output files should be written to
# this is generated if not present yet
path_output = "./data/out/"
# the ner tool - either "flair" or "stanza"
# tool = "flair"
# tool = "stanza"
tool = "transformers"
# please do not modify below this section unless you know what you are doing


def get_sentences(doc):
    # we are only interested in first and last sentence
    # spacy
    text = []
    for sent in doc.sents:
        text.append(str(sent))
    return text


def process_doc(doc, ner_tool="stanza", text=None):
    # remove any named entities
    # stanza
    if ner_tool == "stanza":
        for sent in doc.sentences:
            # entity can be more than one word
            entlist = [ent.text for ent in sent.ents]
            enttype = [ent.type for ent in sent.ents]
            my_sentence = sent.text
            if entlist:
                for ent, etype in zip(entlist, enttype):
                    # find substring in string and replace
                    if etype != "MISC":
                        my_sentence = my_sentence.replace(ent, "[{}]".format(etype))
            newlist = my_sentence.split(" ")
    elif ner_tool == "flair":
        entlist = [
            ent.shortstring.split("/")[0].replace('"', "")
            for ent in doc.get_labels("ner")
        ]
        enttype = [ent.value for ent in doc.get_labels("ner")]
        my_sentence = doc.text
        if entlist:
            for ent, etype in zip(entlist, enttype):
                # find substring in string and replace
                if etype != "MISC":
                    my_sentence = my_sentence.replace(ent, "[{}]".format(etype))
        newlist = my_sentence.split(" ")
    elif ner_tool == "transformers":
        if doc:
            # found named entities
            entlist = []
            newtext = text
            for entity in doc:
                ent_string = entity["entity"]
                # here we could check that string is "I-PER"
                ent_conf = entity["score"]
                ent_position = entity["start"], entity["end"]
                # Here we have to be careful - tokenization with
                # transformers is quite different from spacy/stanza/flair
                # here we get character ids
                entlist.append(ent_position)
                # now replace respective characters
                newtext = newtext[:ent_position[0]] + "x"*(ent_position[1]-ent_position[0]) + newtext[ent_position[1]:]
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


def init_stanza(lang):
    if lang == "fr":
        nlp = sa.Pipeline(
            lang=lang, processors={"ner": "wikiner"}, tokenize_no_ssplit=True
        )
    elif lang == "es":
        nlp = sa.Pipeline(
            lang=lang, processors={"ner": "CoNLL02"}, tokenize_no_ssplit=True
        )
    else:
        ValueError("Language {} not found for Stanza!".format(lang))
    return nlp


def init_flair(lang):
    if lang == "fr":
        ner_string = "fr-ner"
    elif lang == "es":
        ner_string = "es-ner-large"
    else:
        raise ValueError(
            "Currently only en and de models for flair! You selected language {}".format(
                lang
            )
        )
    # nlp = SequenceTagger.load(ner_string)
    # return nlp


def init_transformers():
    # ner_recognizer = pipeline("token-classification")
    ner_recognizer = pipeline("token-classification", model="xlm-roberta-large-finetuned-conll03-english")
    return ner_recognizer

def check_dir(path):
    # check if directory is there
    return os.path.isdir(path)


def make_dir(path):
    # make directory at path
    os.makedirs(path + "/")


if __name__ == "__main__":
    nlp_spacy = init_spacy(lang)
    nlp_stanza = init_stanza(lang)
    nlp_flair = init_flair(lang)
    nlp_transformers = init_transformers()

    # check that input dir is there
    if not check_dir(path_input):
        raise ValueError("Could not find input directory with eml files! Aborting ...")

    # check that the output dir is there, if not generate
    if not check_dir(path_output):
        print("Generating output directory/ies.")
        make_dir(path_output)
    # process the text
    eml_files = in_out.list_of_files(path_input)
    for file in eml_files:
        text = in_out.get_text(path_input + file)
        # skip this text if email could not be parsed
        if not text:
            continue
        text = in_out.delete_header(text)
        doc_spacy = nlp_spacy(text)
        text = get_sentences(doc_spacy)
        # start with first line
        newlist = []
        max_i = 2
        for i in range(0, max_i):
            if tool == "stanza":
                doc = nlp_stanza(text[i])
            if tool == "flair":
                doc = Sentence(text[i])
                nlp_flair.predict(doc)
            if tool == "transformers":
                nlps = nlp_transformers(text[i])
                doc = nlps
            newlist.append(process_doc(doc, ner_tool=tool, text=text[i]))
            newlist[i] = " ".join(newlist[i])
        # join the new and old lines for comparison
        printout = "New: " + " ".join(newlist) + "\n"
        printout = printout + "Old: " + " ".join(text[0:max_i])
        in_out.write_file(printout, path_output + "/" + file)

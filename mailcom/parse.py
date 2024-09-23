import os
import spacy as sp
from transformers import pipeline
from pathlib import Path
from mailcom.inout import InoutHandler
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString

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
    io = InoutHandler(path_input)
    io.list_of_files()
    # html_files = list_of_files(path_input, "html")
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
    xml = dicttoxml(io.email_content["content"])
    # xml = dicttoxml(io.email_content)  Different options for review
    xml_decode = xml.decode()
    xmlfile = open(path_output / "dict.xml", "w")
    xmlfile.write(xml_decode)
    xmlfile.close()
    print(parseString(xml).toprettyxml())
    
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

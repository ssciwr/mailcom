import spacy as sp
import stanza as sa
from flair.data import Sentence
from flair.models import SequenceTagger
import in_out as in_out

# lang = "es"
lang = "fr"
path = "./data/test/"
tool = "flair"


def get_sentences(doc):
    # we are only interested in first and last sentence
    # spacy
    text = []
    for sent in doc.sents:
        text.append(str(sent))
    return text


def process_doc(doc, ner_tool="stanza"):
    # remove any named entities
    # stanza
    if tool == "stanza":
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
    elif tool == "flair":
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
    nlp = SequenceTagger.load(ner_string)
    return nlp


if __name__ == "__main__":
    nlp_spacy = init_spacy(lang)
    nlp_stanza = init_stanza(lang)
    nlp_flair = init_flair(lang)

    # process the text
    eml_files = in_out.list_of_files(path)
    for file in eml_files:
        text = in_out.get_text(path + file)
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
            newlist.append(process_doc(doc, ner_tool=tool))
            newlist[i] = " ".join(newlist[i])
        # join the new and old lines for comparison
        printout = "New: " + " ".join(newlist) + "\n"
        printout = printout + "Old: " + " ".join(text[0:max_i])
        in_out.write_file(printout, "./data/out/" + file)

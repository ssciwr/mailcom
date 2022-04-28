import spacy as sp
import in_out as in_out

lang = "sp"
path = "./data/test/"

def process_doc(doc):
    # we are only interested in first and last sentence
    print(doc)
    # remove any named entities from first and last sentence
    i = 0
    for sent in doc.sents:
        print(sent, i)
        print(sent.ents)
        i = i + 1

if __name__ == "__main__":
    if lang == "sp":
        model = "es_core_news_md"
    elif lang == "fr":
        model = "fr_core_news_md"
    else:
        print("model not found, aborting")
        exit()
    # initialize nlp pipeline
    try:
        nlp = sp.load(model)
    except OSError:
        raise OSError("Could not find {} in standard directory.".format(model))
    nlp = sp.load(model)
    # find which processors are available in model
    components = [component[0] for component in nlp.components]
    print("Loading components {} from {}.".format(components, model))
    # process the text
    eml_files = in_out.list_of_files(path)
    for file in eml_files:
        text = in_out.get_text(path+file)
        text = in_out.delete_header(text)
        doc = nlp(text)
        process_doc(doc)
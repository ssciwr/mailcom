from re import I
import spacy as sp
import stanza as sa
import in_out as in_out

lang = "es"
path = "./data/test/"

def process_doc(doc):
    # we are only interested in first and last sentence
    # remove any named entities from first and last sentence
    i = 0
    # spacy
    # sentences = []
    # for sent in doc.sents:
        # sentences.append(str(sent))
        # if i==0:
            # print(sent, i)
            # print(sent.ents)
            # for token in sent:
                # print(token, token.lemma_, token.tag_, token.ent_type_)
        # i = i + 1
        
    # stanza
    for i, sentence in enumerate(doc.sentences):
        if i==0:
            for word in sentence.words:
                print('{} {} {}'.format(word.text, word.upos, word.lemma))
            print("*************")
            for ent in sentence.ents:
                print("#{} {}".format(ent.text, ent.type))
            print("lllllllllllllll")

def init_spacy(lang):
    if lang == "es":
        # model = "es_core_news_sm"
        model = "es_core_news_md"
        # model = "es_core_news_lg"
        # model = "es_dep_news_trf"
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
    return nlp

def init_stanza(lang):
    nlp = sa.Pipeline(lang=lang, processors='tokenize,mwt,pos,lemma,ner')
    return nlp

if __name__ == "__main__":
    # nlp = init_spacy(lang)
    nlp = init_stanza(lang)
    # process the text
    eml_files = in_out.list_of_files(path)
    for file in eml_files:
        text = in_out.get_text(path+file)
        text = in_out.delete_header(text)
        doc = nlp(text)
        process_doc(doc)
from mailcom import parse
import pytest


# these worked when we were using strings
# with the update to Path, we need to change the tests
def test_check_dir(tmpdir):
    mydir = tmpdir.mkdir("sub")
    assert parse.check_dir(str(mydir))
    with pytest.raises(OSError):
        parse.check_dir(str(tmpdir.join("sub2")))


def test_make_dir(tmpdir):
    mydir = tmpdir.join("sub")
    parse.make_dir(str(mydir))
    assert mydir.check()


def test_check_dir_fail():
    with pytest.raises(OSError):
        parse.check_dir(str("mydir"))


@pytest.fixture()
def get_instant():
    return parse.Pseudonymize()


@pytest.fixture()
def get_default_fr():
    inst = parse.Pseudonymize()
    inst.init_spacy("fr")
    inst.init_transformers()
    return inst


def test_init_spacy(get_instant):
    with pytest.raises(KeyError):
        get_instant.init_spacy("not_a_language")
    with pytest.raises(SystemExit):
        get_instant.init_spacy("fr", "not_an_existing_spacy_model")


def test_init_transformers(get_instant):
    # Test with default model and revision number
    get_instant.init_transformers()
    assert get_instant.ner_recognizer is not None

    # Test with an invalid model
    with pytest.raises(OSError):
        get_instant.init_transformers(model="invalid-model")

    # Test with an invalid revision number
    with pytest.raises(OSError):
        get_instant.init_transformers(
            model="xlm-roberta-large-finetuned-conll03-english",
            model_revision_number="invalid-revision",
        )


def test_reset(get_default_fr):
    text1 = {
        "content": "ceci est un exemple de texte écrit par Claude. Il contient trois noms différents, comme celui de Dominique. Voyons si Martin est reconnu."  # noqa
    }  # noqa
    text2 = {
        "content": "ceci est un exemple de texte écrit par Francois. Il contient trois noms différents, comme celui de Agathe. Voyons si Antoine est reconnu."  # noqa
    }  # noqa
    sample_texts = [text1, text2]
    for text in sample_texts:
        # pseudonymize email
        get_default_fr.pseudonymize(text)
        get_default_fr.reset()
        # Test that used names lists are empty now
        # They should be cleared after every email
        assert len(get_default_fr.ne_list) == 0


def test_get_ner(get_default_fr):
    text = "ceci est un exemple de texte écrit par Claude. Il contient trois noms différents, comme celui de Dominique. Voyons si Martin est reconnu."  # noqa
    sents = get_default_fr.get_sentences(text)
    for sent in sents:
        assert get_default_fr.get_ner(sent)


def test_get_sentences_empty_string(get_default_fr):
    text = ""
    assert get_default_fr.get_sentences(text) == []


def test_get_sentences_multiple_sentences(get_default_fr):
    text = "Ceci est la première phrase. Voici la deuxième phrase. Et enfin, la troisième phrase."  # noqa
    sentences = get_default_fr.get_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "Ceci est la première phrase."
    assert sentences[1] == "Voici la deuxième phrase."
    assert sentences[2] == "Et enfin, la troisième phrase."


def test_get_sentences_with_punctuation(get_default_fr):
    text = "Bonjour! Comment ça va? Très bien, merci."
    sentences = get_default_fr.get_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "Bonjour!"
    assert sentences[1] == "Comment ça va?"
    assert sentences[2] == "Très bien, merci."


def test_pseudonymize_numbers(get_default_fr):
    sentence = "My phone number is 123-456-7890."
    pseudonymized_sentence = get_default_fr.pseudonymize_numbers(sentence)
    assert pseudonymized_sentence == "My phone number is [number]-[number]-[number]."

    sentence = "The year 2023 is almost over."
    pseudonymized_sentence = get_default_fr.pseudonymize_numbers(sentence)
    assert pseudonymized_sentence == "The year [number] is almost over."

    sentence = "No digits here!"
    pseudonymized_sentence = get_default_fr.pseudonymize_numbers(sentence)
    assert pseudonymized_sentence == "No digits here!"

    sentence = ""
    pseudonymized_sentence = get_default_fr.pseudonymize_numbers(sentence)
    assert pseudonymized_sentence == ""


def test_concatenate_empty_list(get_default_fr):
    sentences = []
    concatenated = get_default_fr.concatenate(sentences)
    assert concatenated == ""


def test_concatenate_multiple_sentences(get_default_fr):
    sentences = [
        "This is the first sentence.",
        "This is the second sentence.",
        "This is the third sentence.",
    ]
    concatenated = get_default_fr.concatenate(sentences)
    assert (
        concatenated
        == "This is the first sentence. This is the second sentence. This is the third sentence."  # noqa
    )


def test_pseudonymize(get_default_fr):
    text = {
        "content": "Francois et Agathe sont amis. Mon numéro de téléphone est 123-456-7890."  # noqa
    }
    pseudonymized_text = get_default_fr.pseudonymize(text)

    # Check that names are pseudonymized
    assert "Francois" not in pseudonymized_text
    assert "Agathe" not in pseudonymized_text
    assert any(
        pseudo in pseudonymized_text
        for pseudo in get_default_fr.pseudo_first_names["fr"]
    )

    # Check that numbers are pseudonymized
    assert "123-456-7890" not in pseudonymized_text


def test_pseudonymize_empty_string(get_default_fr):
    text = {"content": ""}
    pseudonymized_text = get_default_fr.pseudonymize(text)
    assert pseudonymized_text == ""


def test_pseudonymize_no_entities(get_default_fr):
    text = {"content": "Ceci est une phrase simple sans entités nommées ni chiffres."}
    pseudonymized_text = get_default_fr.pseudonymize(text)
    assert pseudonymized_text == text["content"]


def test_pseudonymize_email_addresses(get_default_fr):
    sentence = "My email is example@example.com."
    pseudonymized_sentence = get_default_fr.pseudonymize_email_addresses(sentence)
    assert pseudonymized_sentence == "My email is [email]"

    sentence = "Contact us at support@example.com or sales@example.com."
    pseudonymized_sentence = get_default_fr.pseudonymize_email_addresses(sentence)
    assert pseudonymized_sentence == "Contact us at [email] or [email]"

    sentence = "No email addresses here!"
    pseudonymized_sentence = get_default_fr.pseudonymize_email_addresses(sentence)
    assert pseudonymized_sentence == "No email addresses here!"

    sentence = ""
    pseudonymized_sentence = get_default_fr.pseudonymize_email_addresses(sentence)
    assert pseudonymized_sentence == ""


def test_choose_per_pseudonym_new_name(get_default_fr):
    name = "Jean"
    pseudonym = get_default_fr.choose_per_pseudonym(name)
    assert pseudonym in get_default_fr.pseudo_first_names["fr"]


def test_choose_per_pseudonym_existing_name(get_default_fr):
    name = "Claude"
    get_default_fr.ne_list = [
        {"word": "Claude", "entity_group": "PER", "pseudonym": "Dominique"}
    ]
    pseudonym = get_default_fr.choose_per_pseudonym(name)
    assert pseudonym == "Dominique"


def test_choose_per_pseudonym_case_insensitive(get_default_fr):
    name = "claude"
    get_default_fr.ne_list = [
        {"word": "Claude", "entity_group": "PER", "pseudonym": "Dominique"}
    ]
    pseudonym = get_default_fr.choose_per_pseudonym(name)
    assert pseudonym == "Dominique"


def test_choose_per_pseudonym_exhausted_list(get_default_fr):
    name = "Jean"
    get_default_fr.ne_list = [
        {"word": "Claude", "entity_group": "PER", "pseudonym": pseudo}
        for pseudo in get_default_fr.pseudo_first_names["fr"]
    ]
    pseudonym = get_default_fr.choose_per_pseudonym(name)
    assert pseudonym == get_default_fr.pseudo_first_names["fr"][0]


def test_pseudonymize_ne_person(get_default_fr):
    sentence = "Mehdi et Théo sont amis."
    ner = [
        {"entity_group": "PER", "word": "Mehdi", "start": 0, "end": 5},
        {"entity_group": "PER", "word": "Théo", "start": 9, "end": 13},
    ]
    pseudonymized_sentence = " ".join(get_default_fr.pseudonymize_ne(ner, sentence))
    assert "Mehdi" not in pseudonymized_sentence
    assert "Théo" not in pseudonymized_sentence
    assert any(
        pseudo in pseudonymized_sentence
        for pseudo in get_default_fr.pseudo_first_names["fr"]
    )


def test_pseudonymize_ne_location(get_default_fr):
    sentence = "Paris est une belle ville."
    ner = [
        {"entity_group": "LOC", "word": "Paris", "start": 0, "end": 5},
    ]
    pseudonymized_sentence = " ".join(get_default_fr.pseudonymize_ne(ner, sentence))
    assert pseudonymized_sentence == "[location] est une belle ville."


def test_pseudonymize_ne_organization(get_default_fr):
    sentence = "Microsoft est une grande entreprise."
    ner = [
        {"entity_group": "ORG", "word": "Microsoft", "start": 0, "end": 9},
    ]
    pseudonymized_sentence = " ".join(get_default_fr.pseudonymize_ne(ner, sentence))
    assert pseudonymized_sentence == "[organization] est une grande entreprise."


def test_pseudonymize_ne_misc(get_default_fr):
    sentence = "Le Tour de France est un événement célèbre."
    ner = [
        {"entity_group": "MISC", "word": "Tour de France", "start": 3, "end": 17},
    ]
    pseudonymized_sentence = " ".join(get_default_fr.pseudonymize_ne(ner, sentence))
    assert pseudonymized_sentence == "Le [misc] est un événement célèbre."


def test_pseudonymize_ne_multiple_entities(get_default_fr):
    sentence = "Thomas travaille chez Microsoft à Paris."
    ner = [
        {"entity_group": "PER", "word": "Thomas", "start": 0, "end": 6},
        {"entity_group": "ORG", "word": "Microsoft", "start": 18, "end": 27},
        {"entity_group": "LOC", "word": "Paris", "start": 30, "end": 35},
    ]
    pseudonymized_sentence = " ".join(get_default_fr.pseudonymize_ne(ner, sentence))
    assert "Thomas" not in pseudonymized_sentence
    assert "Microsoft" not in pseudonymized_sentence
    assert "Paris" not in pseudonymized_sentence
    assert any(
        pseudo in pseudonymized_sentence
        for pseudo in get_default_fr.pseudo_first_names["fr"]
    )
    assert "[organization]" in pseudonymized_sentence
    assert "[location]" in pseudonymized_sentence


def test_pseudonymize_ne_no_entities(get_default_fr):
    sentence = "Ceci est une phrase sans entités nommées."
    ner = []
    pseudonymized_sentence = " ".join(get_default_fr.pseudonymize_ne(ner, sentence))
    assert pseudonymized_sentence == sentence


def test_pseudonymize_ne_empty_sentence(get_default_fr):
    sentence = "Ceci est une phrase sans entités nommées."
    ner = []
    pseudonymized_sentence = " ".join(get_default_fr.pseudonymize_ne(ner, sentence))
    assert pseudonymized_sentence == sentence

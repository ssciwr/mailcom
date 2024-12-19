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
    text1 = "ceci est un exemple de texte écrit par Claude. Il contient trois noms différents, comme celui de Dominique. Voyons si Martin est reconnu."  # noqa
    text2 = "ceci est un exemple de texte écrit par Francois. Il contient trois noms différents, comme celui de Agathe. Voyons si Antoine est reconnu."  # noqa
    sample_texts = [text1, text2]
    for text in sample_texts:
        # pseudonymize email
        get_default_fr.pseudonymize(text)
        get_default_fr.reset()
        # Test that used names lists are empty now
        # They should be cleared after every email
        assert len(get_default_fr.used_first_names) == 0


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


def test_pseudonymize_per(get_default_fr):
    sentence = "Francois and Agathe are friends."
    nelist = ["Francois", "Agathe"]
    pseudonymized_sentence = get_default_fr.pseudonymize_per(sentence, nelist)
    assert "Francois" not in pseudonymized_sentence
    assert "Agathe" not in pseudonymized_sentence
    assert any(
        pseudo in pseudonymized_sentence
        for pseudo in get_default_fr.pseudo_first_names["fr"]
    )


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
    text = "Francois et Agathe sont amis. Mon numéro de téléphone est 123-456-7890."
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
    text = ""
    pseudonymized_text = get_default_fr.pseudonymize(text)
    assert pseudonymized_text == ""


def test_pseudonymize_no_entities(get_default_fr):
    text = "Ceci est une phrase simple sans entités nommées ni chiffres."
    pseudonymized_text = get_default_fr.pseudonymize(text)
    assert pseudonymized_text == text


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


def test_pseudonymize_ne_with_person_entities(get_default_fr):
    sentence = "Francois et Agathe sont amis."
    ner = [
        {
            "entity_group": "PER",
            "score": 0.99,
            "word": "Francois",
            "start": 0,
            "end": 8,
        },
        {
            "entity_group": "PER",
            "score": 0.99,
            "word": "Agathe",
            "start": 13,
            "end": 19,
        },
    ]
    pseudonymized_sentence = get_default_fr.pseudonymize_ne(ner, sentence)
    assert "Francois" not in pseudonymized_sentence[0]
    assert "Agathe" not in pseudonymized_sentence[0]
    assert any(
        pseudo in pseudonymized_sentence[0]
        for pseudo in get_default_fr.pseudo_first_names["fr"]
    )


def test_pseudonymize_ne_with_location_entities(get_default_fr):
    sentence = "Paris et New York sont des villes."
    ner = [
        {
            "entity_group": "LOC",
            "score": 0.99,
            "word": "Paris",
            "start": 0,
            "end": 5,
        },
        {
            "entity_group": "LOC",
            "score": 0.99,
            "word": "New York",
            "start": 10,
            "end": 18,
        },
    ]
    pseudonymized_sentence = get_default_fr.pseudonymize_ne(ner, sentence)
    assert "Paris" not in pseudonymized_sentence[0]
    assert "New York" not in pseudonymized_sentence[0]
    assert "[location]" in pseudonymized_sentence[0]


def test_pseudonymize_ne_with_organization_entities(get_default_fr):
    sentence = "Google et Microsoft sont des géants de la technologie."
    ner = [
        {
            "entity_group": "ORG",
            "score": 0.99,
            "word": "Google",
            "start": 0,
            "end": 6,
        },
        {
            "entity_group": "ORG",
            "score": 0.99,
            "word": "Microsoft",
            "start": 11,
            "end": 20,
        },
    ]
    pseudonymized_sentence = get_default_fr.pseudonymize_ne(ner, sentence)
    assert "Google" not in pseudonymized_sentence[0]
    assert "Microsoft" not in pseudonymized_sentence[0]
    assert "[organization]" in pseudonymized_sentence[0]


def test_pseudonymize_ne_with_misc_entities(get_default_fr):
    sentence = "La tour Eiffel est un monument célèbre."
    ner = [
        {
            "entity_group": "MISC",
            "score": 0.99,
            "word": "tour Eiffel",
            "start": 4,
            "end": 16,
        },
    ]
    pseudonymized_sentence = get_default_fr.pseudonymize_ne(ner, sentence)
    assert "tour Eiffel" not in pseudonymized_sentence[0]
    assert "[misc]" in pseudonymized_sentence[0]


def test_set_sentence_batch_size(get_default_fr):
    # Test with valid batch sizes
    get_default_fr.set_sentence_batch_size(1)
    assert get_default_fr.n_batch_sentences == 1

    get_default_fr.set_sentence_batch_size(10)
    assert get_default_fr.n_batch_sentences == 10

    get_default_fr.set_sentence_batch_size(-1)
    assert get_default_fr.n_batch_sentences == -1

    # Test with invalid batch sizes
    with pytest.raises(ValueError):
        get_default_fr.set_sentence_batch_size(0)

    with pytest.raises(ValueError):
        get_default_fr.set_sentence_batch_size(-2)

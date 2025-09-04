from mailcom import parse
import pytest
from mailcom.utils import TransformerLoader, SpacyLoader


@pytest.fixture()
def get_pseudo_first_names():
    return {
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


@pytest.fixture()
def get_instant(get_pseudo_first_names):
    return parse.Pseudonymize(get_pseudo_first_names)


@pytest.fixture()
def get_default_w_spacy(get_pseudo_first_names):
    spacy_loader = SpacyLoader()
    inst = parse.Pseudonymize(get_pseudo_first_names, spacy_loader=spacy_loader)
    return inst


@pytest.fixture()
def get_default_fr(get_pseudo_first_names):
    trans_loader = TransformerLoader()
    spacy_loader = SpacyLoader()
    inst = parse.Pseudonymize(
        get_pseudo_first_names, trans_loader=trans_loader, spacy_loader=spacy_loader
    )
    inst.init_spacy("fr")
    return inst


def test_init_spacy_none(get_instant):
    with pytest.raises(ValueError):
        get_instant.init_spacy("de", "default")


def test_init_spacy_not_none(get_default_w_spacy):
    get_default_w_spacy.init_spacy("fr")
    assert get_default_w_spacy.nlp_spacy is not None

    get_default_w_spacy.init_spacy("de_is_default")
    assert get_default_w_spacy.nlp_spacy is not None


def test_init_spacy_invalid_model(get_default_w_spacy):
    with pytest.raises(SystemExit):
        get_default_w_spacy.init_spacy("fr", "not_an_existing_spacy_model")


def test_init_spacy_implicit(get_default_w_spacy):
    get_default_w_spacy.get_sentences("Ceci est un exemple de texte.", language="fr")
    assert get_default_w_spacy.nlp_spacy is not None


def test_init_transformers_none(get_instant):
    with pytest.raises(ValueError):
        get_instant.init_transformers()


def test_init_transformers_not_none(get_default_fr):
    get_default_fr.init_transformers()
    assert get_default_fr.ner_recognizer is not None


def test_init_transformers_invalid_key(get_default_fr):
    get_default_fr.feature = "not_a_key"
    with pytest.raises(ValueError):
        get_default_fr.init_transformers()


def test_init_transformers_new_settings(get_default_fr):
    # correct case
    get_default_fr.init_transformers(pipeline_info={"task": "token-classification"})
    assert get_default_fr.ner_recognizer is not None

    # invalid case
    get_default_fr.feature = "typeerror"
    with pytest.raises(TypeError):
        get_default_fr.init_transformers(pipeline_info="invalid-setting-info")
    get_default_fr.feature = "runtimeerror"
    with pytest.raises(RuntimeError):
        get_default_fr.init_transformers(pipeline_info={"test": "test"})
    get_default_fr.feature = "keyerror"
    with pytest.raises(KeyError):
        get_default_fr.init_transformers(pipeline_info={"task": "invalid-task"})


def test_reset(get_default_fr):
    text1 = {
        "content": "ceci est un exemple de texte écrit par Claude. "
        "Il contient trois noms différents, comme celui de Dominique. "
        "Voyons si Martin est reconnu."  # noqa
    }  # noqa
    text2 = {
        "content": "ceci est un exemple de texte écrit par Francois. "
        "Il contient trois noms différents, comme celui de Agathe. "
        "Voyons si Antoine est reconnu."  # noqa
    }  # noqa
    sample_texts = [text1, text2]
    for text in sample_texts:
        # pseudonymize email
        get_default_fr.pseudonymize(text["content"], language="fr")
        get_default_fr.reset()
        # Test that used names lists are empty now
        # They should be cleared after every email
        assert len(get_default_fr.ne_list) == 0
        assert len(get_default_fr.ne_sent) == 0
        assert len(get_default_fr.sentences) == 0


def test_get_ne_sent_dict(get_default_fr):
    text = {"content": "Francois et Agathe vont à Paris."}
    _ = get_default_fr.pseudonymize(text["content"], language="fr")
    assert get_default_fr.ne_sent == [0, 0, 0]
    assert get_default_fr.ne_list[0]["entity_group"] == "PER"
    assert get_default_fr.ne_list[0]["word"] == "Francois"
    assert get_default_fr.ne_list[2]["word"] == "Paris"
    ne_sent_dict = get_default_fr._get_ne_sent_dict()
    assert ne_sent_dict["0"][0]["entity_group"] == "PER"
    assert ne_sent_dict["0"][1]["word"] == "Agathe"
    assert ne_sent_dict["0"][2]["start"] == 26


def test_get_ner(get_default_fr):
    text = (
        "ceci est un exemple de texte écrit par Claude. "
        "Il contient trois noms différents, comme celui de Dominique. "
        "Voyons si Martin est reconnu."
    )  # noqa
    sents = get_default_fr.get_sentences(text, "fr")
    for sent in sents:
        assert get_default_fr.get_ner(sent)


def test_check_pseudonyms_in_content(get_default_fr):
    get_default_fr.ne_list = [{"entity_group": "PER", "word": "Agathe"}]
    assert not get_default_fr._check_pseudonyms_in_content()
    get_default_fr.ne_list = [{"entity_group": "PER", "word": "Claude"}]
    assert get_default_fr._check_pseudonyms_in_content()
    assert "Claude" not in get_default_fr.pseudo_first_names


def test_get_sentences_empty_string(get_default_fr):
    text = ""
    assert get_default_fr.get_sentences(text, "fr") == []
    assert "sentencizer" in get_default_fr.nlp_spacy.pipe_names


def test_get_sentences_multiple_sentences(get_default_fr):
    text = (
        "Ceci est la première phrase. "
        "Voici la deuxième phrase. Et enfin, la troisième phrase."
    )  # noqa
    sentences = get_default_fr.get_sentences(text, "fr")
    assert len(sentences) == 3
    assert sentences[0] == "Ceci est la première phrase."
    assert sentences[1] == "Voici la deuxième phrase."
    assert sentences[2] == "Et enfin, la troisième phrase."
    assert "sentencizer" in get_default_fr.nlp_spacy.pipe_names


def test_get_sentences_with_punctuation(get_default_fr):
    text = "Bonjour! Comment ça va? Très bien, merci."
    sentences = get_default_fr.get_sentences(text, "fr")
    assert len(sentences) == 3
    assert sentences[0] == "Bonjour!"
    assert sentences[1] == "Comment ça va?"
    assert sentences[2] == "Très bien, merci."
    assert "sentencizer" in get_default_fr.nlp_spacy.pipe_names


def test_get_letter_indices_non_empty(get_default_fr):
    sentence = (
        "The test date is 27.03.2025 13:37 and the other date is 01.01.2022. "
        "Repeating one more time 27.03.2025 13:37."
    )
    detected_dates = ["27.03.2025 13:37", "01.01.2022"]

    date_indices = get_default_fr._get_letter_indices(sentence, detected_dates)
    expected_indices = set()
    expected_indices.update(range(17, 33))
    expected_indices.update(range(92, 108))
    expected_indices.update(range(56, 66))
    assert date_indices == expected_indices


def test_get_letter_indices_empty(get_default_fr):
    sentence = "This is a test"
    detected_dates = ["27.03.2025 13:37", "01.01.2022"]
    assert get_default_fr._get_letter_indices(sentence, detected_dates) == set()


def test_test_get_letter_indices_no_dates(get_default_fr):
    sentence = "This is another test"
    detected_dates = []
    assert get_default_fr._get_letter_indices(sentence, detected_dates) == set()

    detected_dates = None
    assert get_default_fr._get_letter_indices(sentence, detected_dates) == set()


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


def test_pseudonymize_numbers_with_dates(get_default_fr):
    sentence = "The test date is 27.03.2025 13:37 with number 123-456-789."
    detected_dates = ["27.03.2025 13:37"]
    pseudonymized_sentence = get_default_fr.pseudonymize_numbers(
        sentence, detected_dates
    )
    assert (
        pseudonymized_sentence
        == "The test date is 27.03.2025 13:37 with number [number]-[number]-[number]."
    )

    pseudonymized_sentence = get_default_fr.pseudonymize_numbers(
        sentence, detected_dates=None
    )
    assert (
        pseudonymized_sentence
        == "The test date is [number].[number].[number] [number]:[number] "
        "with number [number]-[number]-[number]."
    )

    sentence = "No number"
    detected_dates = ["27.03.2025 13:37"]
    pseudonymized_sentence = get_default_fr.pseudonymize_numbers(
        sentence, detected_dates
    )
    assert pseudonymized_sentence == "No number"


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
        concatenated == "This is the first sentence. "
        "This is the second sentence. "
        "This is the third sentence."  # noqa
    )


def test_pseudonymize(get_default_fr):
    text = {
        "content": "Francois et Agathe sont amis. "
        "Mon numéro de téléphone est 123-456-7890."  # noqa
    }
    pseudonymized_text, _ = get_default_fr.pseudonymize(text["content"], language="fr")

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
    pseudonymized_text, _ = get_default_fr.pseudonymize(text["content"], language="fr")
    assert pseudonymized_text == ""


def test_pseudonymize_no_entities(get_default_fr):
    text = {"content": "Ceci est une phrase simple sans entités nommées ni chiffres."}
    pseudonymized_text, _ = get_default_fr.pseudonymize(text["content"], language="fr")
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


def test_choose_per_pseudonym_different_language(get_default_fr):
    name = "John"

    # exhausted list
    get_default_fr.ne_list = [
        {"word": "Claude", "entity_group": "PER", "pseudonym": pseudo}
        for pseudo in get_default_fr.pseudo_first_names["es"]
    ]
    pseudonym = get_default_fr.choose_per_pseudonym(name, lang="gl")
    assert pseudonym == get_default_fr.pseudo_first_names["es"][0]


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


def test_pseudonymize_with_updated_ne(get_default_fr):
    sentences = [
        "Le Tour de France est un événement célèbre.",
        "Thomas travaille chez Microsoft à Paris.",
    ]
    ner_sent_dict = {
        "0": [
            {"entity_group": "MISC", "word": "Tour de France", "start": 3, "end": 17},
        ],
        "1": [
            {"entity_group": "PER", "word": "Thomas", "start": 0, "end": 6},
            {"entity_group": "ORG", "word": "Microsoft", "start": 18, "end": 27},
            {"entity_group": "LOC", "word": "Paris", "start": 30, "end": 35},
        ],
    }
    pseudonymized_sentence, _ = get_default_fr.pseudonymize_with_updated_ne(
        sentences, ner_sent_dict, language="fr", detected_dates=None
    )

    assert "Tour de France" not in pseudonymized_sentence
    assert "Thomas" not in pseudonymized_sentence
    assert "Microsoft" not in pseudonymized_sentence
    assert "Paris" not in pseudonymized_sentence
    assert any(
        pseudo in pseudonymized_sentence
        for pseudo in get_default_fr.pseudo_first_names["fr"]
    )
    assert "[organization]" in pseudonymized_sentence
    assert "[location]" in pseudonymized_sentence
    assert "[misc]" in pseudonymized_sentence


def test_pseudonymize_for_same_pseudo_and_name(get_default_fr):
    text = {
        "content": "Claude et Camille sont amis. "
        "Mon numéro de téléphone est 123-456-7890."  # noqa
    }
    pseudonymized_text, exclude_pseudonym = get_default_fr.pseudonymize(
        text["content"], language="fr"
    )
    assert exclude_pseudonym
    assert "Claude" not in get_default_fr.pseudo_first_names
    assert "Camille" not in get_default_fr.pseudo_first_names
    # now re-pseudonymize with the correct pseudonyms
    pseudonymized_text, exclude_pseudonym = get_default_fr.pseudonymize_with_updated_ne(
        text["content"], ne_sent_dict=None, language="fr"
    )
    assert "Claude" not in pseudonymized_text
    assert "Camille" not in pseudonymized_text
    assert any(
        pseudo in pseudonymized_text
        for pseudo in get_default_fr.pseudo_first_names["fr"]
    )
    # Check that numbers are pseudonymized
    assert "123-456-7890" not in pseudonymized_text
    # check that all properties required for the processing dict are there
    assert get_default_fr.sentences == text["content"]
    assert get_default_fr.ne_list
    assert get_default_fr.ne_sent

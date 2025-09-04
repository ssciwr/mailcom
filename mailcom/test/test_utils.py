from mailcom import utils
import pytest


def test_check_dir(tmpdir):
    mydir = tmpdir.mkdir("sub")
    assert utils.check_dir(mydir)
    with pytest.raises(OSError):
        utils.check_dir(tmpdir.join("sub2"))


def test_make_dir(tmpdir):
    mydir = tmpdir.join("sub")
    utils.make_dir(mydir)
    assert mydir.check()


def test_check_dir_fail():
    with pytest.raises(OSError):
        utils.check_dir("mydir")


def test_clean_up_content():
    sent_1 = "Hello, how are you?"
    sent_2 = "I'm fine, thank you."
    expected_text = "Hello, how are you?\nI'm fine, thank you."
    assert (
        utils.clean_up_content(sent_1 + "\n\n\n" + sent_2 + "\n\n")[0] == expected_text
    )
    assert (
        utils.clean_up_content("      " + sent_1 + "\n" + sent_2 + "      ")[0]
        == expected_text
    )
    assert (
        utils.clean_up_content("      " + sent_1 + "\n\n" + sent_2 + "      ")[0]
        == expected_text
    )


@pytest.fixture()
def get_spacy_loader():
    return utils.SpacyLoader()


def test_get_default_model(get_spacy_loader):
    lang, model = get_spacy_loader.get_default_model("fr")
    assert lang == "fr"
    assert model == "fr_core_news_md"

    lang, model = get_spacy_loader.get_default_model("de_is_default")
    assert lang == "de"
    assert model == "de_core_news_md"

    lang, model = get_spacy_loader.get_default_model("gl")
    assert lang == "pt"
    assert model == "pt_core_news_md"


def test_init_spacy(get_spacy_loader):
    # correct cases
    get_spacy_loader.init_spacy("fr")
    assert get_spacy_loader.spacy_instances["fr"]["fr_core_news_md"] is not None

    # default language
    get_spacy_loader.init_spacy("de_is_default")
    assert get_spacy_loader.spacy_instances["de"]["de_core_news_md"] is not None

    # invalid case
    with pytest.raises(SystemExit):
        get_spacy_loader.init_spacy("fr", "not_an_existing_spacy_model")


def test_get_spacy_instance(get_spacy_loader):
    # none case
    with pytest.raises(ValueError):
        utils.get_spacy_instance(None, "fr", "default")

    # correct cases
    assert utils.get_spacy_instance(get_spacy_loader, "fr", "default") is not None
    assert (
        utils.get_spacy_instance(get_spacy_loader, "fr", "fr_core_news_md") is not None
    )
    assert utils.get_spacy_instance(get_spacy_loader, "es", "default") is not None
    assert (
        utils.get_spacy_instance(get_spacy_loader, "es", "es_core_news_md") is not None
    )

    # default language
    assert (
        utils.get_spacy_instance(get_spacy_loader, "de_is_default", "default")
        is not None
    )

    # invalid case
    with pytest.raises(SystemExit):
        utils.get_spacy_instance(get_spacy_loader, "fr", "not_an_existing_spacy_model")


@pytest.fixture()
def get_transformer_loader():
    return utils.TransformerLoader()


def test_init_transformers_none_settings(get_transformer_loader):
    # correct features
    get_transformer_loader.init_transformers(feature="ner")
    assert get_transformer_loader.trans_instances["ner"] is not None
    get_transformer_loader.init_transformers(feature="lang_detector")
    assert get_transformer_loader.trans_instances["lang_detector"] is not None

    # invalid feature
    with pytest.raises(ValueError):
        get_transformer_loader.init_transformers(feature="invalid-feature")


def test_init_transformers_new_settings(get_transformer_loader):
    # correct case
    get_transformer_loader.init_transformers(
        feature="test", pipeline_info={"task": "text-classification"}
    )
    assert get_transformer_loader.trans_instances["test"] is not None

    # invalid case
    with pytest.raises(KeyError):
        get_transformer_loader.init_transformers(
            feature="test", pipeline_info={"task": "invalid-task"}
        )
    with pytest.raises(TypeError):
        get_transformer_loader.init_transformers(
            feature="test", pipeline_info="invalid-setting-info"
        )
    with pytest.raises(RuntimeError):
        get_transformer_loader.init_transformers(
            feature="test", pipeline_info={"test": "test"}
        )


def test_get_trans_instance(get_transformer_loader):
    # none case
    with pytest.raises(ValueError):
        utils.get_trans_instance(None, "ner")

    # correct cases
    assert utils.get_trans_instance(get_transformer_loader, "ner") is not None
    assert utils.get_trans_instance(get_transformer_loader, "lang_detector") is not None

    # invalid case
    with pytest.raises(ValueError):
        utils.get_trans_instance(get_transformer_loader, "invalid-feature")


def test_highlight_ne_sent():
    text = "Hello, my name is John Doe."
    ne_list = [{"word": "John Doe", "start": 18, "end": 26, "entity_group": "PERSON"}]
    colors = {"PERSON": "lightblue"}
    result = utils.highlight_ne_sent(text, ne_list, colors)
    expected = (
        'Hello, my name is <span style="background-color:lightblue">John Doe</span>.'
    )
    assert result == expected
    text = "I am a Research Software Engineer at the Scientific Software Center. Most of my time I spend in Heidelberg, writing tests for Python packages."  # noqa
    ne_list = [
        {
            "word": "Research Software Engineer",
            "start": 7,
            "end": 33,
            "entity_group": "PERSON",
        },
        {
            "word": "Scientific Software Center",
            "start": 41,
            "end": 67,
            "entity_group": "ORG",
        },
        {"word": "Heidelberg", "start": 96, "end": 106, "entity_group": "LOC"},
        {"word": "Python", "start": 126, "end": 132, "entity_group": "MISC"},
    ]
    colors = {
        "PERSON": "lightblue",
        "ORG": "lightgreen",
        "LOC": "lightyellow",
        "MISC": "lightpink",
    }
    result = utils.highlight_ne_sent(text, ne_list, colors)
    expected = 'I am a <span style="background-color:lightblue">Research Software Engineer</span> at the <span style="background-color:lightgreen">Scientific Software Center</span>. Most of my time I spend in <span style="background-color:lightyellow">Heidelberg</span>, writing tests for <span style="background-color:lightpink">Python</span> packages.'  # noqa
    assert result == expected
    # test if no color was assigned for entity
    colors = {}
    result = utils.highlight_ne_sent(text, ne_list, colors)
    expected = 'I am a <span style="background-color:lightgray">Research Software Engineer</span> at the <span style="background-color:lightgray">Scientific Software Center</span>. Most of my time I spend in <span style="background-color:lightgray">Heidelberg</span>, writing tests for <span style="background-color:lightgray">Python</span> packages.'  # noqa
    assert result == expected
    # test with no named entities
    text = "I am a Research Software Engineer at the Scientific Software Center."
    ne_list = []
    colors = {
        "PERSON": "lightblue",
        "ORG": "lightgreen",
        "LOC": "lightyellow",
        "MISC": "lightpink",
    }
    result = utils.highlight_ne_sent(text, ne_list, colors)
    assert result == text
    # with same entry multiple times
    text = "Hello, my name is John Doe. You can call me John Doe."
    ne_list = [
        {"word": "John Doe", "start": 18, "end": 26, "entity_group": "PERSON"},
        {"word": "John Doe", "start": 44, "end": 52, "entity_group": "PERSON"},
    ]
    colors = {"PERSON": "lightblue"}
    result = utils.highlight_ne_sent(text, ne_list, colors)
    expected = 'Hello, my name is <span style="background-color:lightblue">John Doe</span>. You can call me <span style="background-color:lightblue">John Doe</span>.'  # noqa
    assert result == expected
    # missing keys in ne_list
    ne_list = [
        {"word": "John Doe", "start": 18, "end": 26, "entity_group": "PERSON"},
        {"word": "John Doe", "start": 44, "end": 52},
    ]
    with pytest.raises(ValueError):
        utils.highlight_ne_sent(text, ne_list, colors)

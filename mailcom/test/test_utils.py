import math
from mailcom import utils
import pytest
from string import punctuation
import datetime


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


def test_init_spacy(get_spacy_loader):
    get_spacy_loader.init_spacy("use_default")
    assert get_spacy_loader.nlp_spacy is not None
    with pytest.raises(SystemExit):
        get_spacy_loader.init_spacy("fr", "not_an_existing_spacy_model")

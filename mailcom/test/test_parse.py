from mailcom import parse, inout
import pytest
from pathlib import Path
from importlib import resources

pkg = resources.files("mailcom")

FILE_PATH = Path(pkg / "test" / "data")


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


@pytest.fixture()
def get_sample_texts():
    inst = inout.InoutHandler(FILE_PATH)
    inst.list_of_files()
    email_list = []
    for file in inst.email_list:
        text = inst.get_text(file)
        text = inst.get_html_text(text)
        if not text:
            continue
        email_list.append(text)
    return email_list


def test_init_spacy(get_instant):
    with pytest.raises(KeyError):
        get_instant.init_spacy("not_a_language")
    with pytest.raises(OSError):
        get_instant.init_spacy("fr", "not_an_existing_spacy_model")


# TODO init_transformers


def test_reset(get_default_fr, get_sample_texts):
    for text in get_sample_texts:
        # Test that used names lists are empty
        # They should be cleared after every email
        assert len(get_default_fr.used_first_names) == 0
        assert len(get_default_fr.used_last_names) == 0
        # pseudonymize email
        get_default_fr.pseudonymize(text)

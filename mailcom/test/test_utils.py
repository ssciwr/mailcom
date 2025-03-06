from mailcom import utils
import pytest


# these worked when we were using strings
# with the update to Path, we need to change the tests
def test_check_dir(tmpdir):
    mydir = tmpdir.mkdir("sub")
    assert utils.check_dir(str(mydir))
    with pytest.raises(OSError):
        utils.check_dir(str(tmpdir.join("sub2")))


def test_make_dir(tmpdir):
    mydir = tmpdir.join("sub")
    utils.make_dir(str(mydir))
    assert mydir.check()


def test_check_dir_fail():
    with pytest.raises(OSError):
        utils.check_dir(str("mydir"))


langid_langs = ['af', 'am', 'an', 'ar', 'as', 'az', 
                    'be', 'bg', 'bn', 'br', 'bs', 
                    'ca', 'cs', 'cy', 
                    'da', 'de', 'dz', 
                    'el', 'en', 'eo', 'es', 'et', 'eu', 
                    'fa', 'fi', 'fo', 'fr', 
                    'ga', 'gl', 'gu', 
                    'he', 'hi', 'hr', 'ht', 'hu', 'hy', 
                    'id', 'is', 'it', 
                    'ja', 'jv', 
                    'ka', 'kk', 'km', 'kn', 'ko', 'ku', 'ky', 
                    'la', 'lb', 'lo', 'lt', 'lv', 
                    'mg', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt', 
                    'nb', 'ne', 'nl', 'nn', 'no', 
                    'oc', 'or', 
                    'pa', 'pl', 'ps', 'pt', 
                    'qu', 
                    'ro', 'ru', 'rw', 
                    'se', 'si', 'sk', 'sl', 'sq', 'sr', 'sv', 'sw', 
                    'ta', 'te', 'th', 'tl', 'tr', 
                    'ug', 'uk', 'ur', 
                    'vi', 'vo', 
                    'wa', 
                    'xh', 
                    'zh', 'zu']


@pytest.fixture()
def get_lang_detector():
    return utils.LangDetector()


def test_lang_detector(get_lang_detector):
    assert get_lang_detector.lang_id.nb_classes == langid_langs


def test_constrain_langid(get_lang_detector):
    lang_set = ["es", "fr"]
    get_lang_detector.constrain_langid(lang_set)
    assert get_lang_detector.lang_id.nb_classes == lang_set


def test_constrain_langid_empty(get_lang_detector):
    lang_set = []
    get_lang_detector.constrain_langid(lang_set)
    assert get_lang_detector.lang_id.nb_classes == langid_langs


def test_constrain_langid_intersec(get_lang_detector):
    lang_set = ["es", "fr", "not_a_language"]
    get_lang_detector.constrain_langid(lang_set)
    assert get_lang_detector.lang_id.nb_classes == ["es", "fr"]


def test_constrain_langid_fail(get_lang_detector):
    lang_set = ["not_a_language"]
    with pytest.raises(ValueError):
        get_lang_detector.constrain_langid(lang_set)
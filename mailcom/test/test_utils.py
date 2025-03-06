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


lang_samples = [
    "J'espère que tu vas bien! Je voulais partager avec toi quelques photos de mon dernier voyage!",
    "Hola, ¿cómo estás? Espero que estés bien. ¡Hasta pronto!",
    "Bonjour, comment ça va? J'espère que tu vas bien. À bientôt!",
    "Hello, how are you? I hope you are well. See you soon!",
    "Hallo, wie geht es dir? Ich hoffe, es geht dir gut. Bis bald!",
    "Ciao, come stai? Spero che tu stia bene. A presto!",
    "Olá, como você está? Espero que você esteja bem. Até logo!",
    "Привет, как дела? Надеюсь, у тебя все хорошо. Увидимся скоро!",
    "你好，你好吗？希望你一切都好。很快见到你！",
    "こんにちは、元気ですか？ あなたが元気であることを願っています。 またね！",
    "안녕하세요, 어떻게 지내세요? 잘 지내길 바랍니다. 곧 뵙겠습니다!",
]


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


def test_determine_langdetect(get_lang_detector):
    get_lang_detector.determine_langdetect()
    probs = []
    for i in range(10):
        _, prob = get_lang_detector.detect_with_langdetect(lang_samples[0])
        probs.append(prob)
    assert len(set(probs)) == 1


def test_detect_with_langid(get_lang_detector):
    lang, prob = get_lang_detector.detect_with_langid(lang_samples[0])
    assert lang == "fr"
    assert prob > 0.9


def test_detect_with_langdetect(get_lang_detector):
    get_lang_detector.determine_langdetect()
    lang, prob = get_lang_detector.detect_with_langdetect(lang_samples[0])
    assert lang == "fr"
    assert prob > 0.9
import math
from mailcom import utils
import pytest
from string import punctuation


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


# test cases for email language detection
LANGID_LANGS = [
    "af",
    "am",
    "an",
    "ar",
    "as",
    "az",
    "be",
    "bg",
    "bn",
    "br",
    "bs",
    "ca",
    "cs",
    "cy",
    "da",
    "de",
    "dz",
    "el",
    "en",
    "eo",
    "es",
    "et",
    "eu",
    "fa",
    "fi",
    "fo",
    "fr",
    "ga",
    "gl",
    "gu",
    "he",
    "hi",
    "hr",
    "ht",
    "hu",
    "hy",
    "id",
    "is",
    "it",
    "ja",
    "jv",
    "ka",
    "kk",
    "km",
    "kn",
    "ko",
    "ku",
    "ky",
    "la",
    "lb",
    "lo",
    "lt",
    "lv",
    "mg",
    "mk",
    "ml",
    "mn",
    "mr",
    "ms",
    "mt",
    "nb",
    "ne",
    "nl",
    "nn",
    "no",
    "oc",
    "or",
    "pa",
    "pl",
    "ps",
    "pt",
    "qu",
    "ro",
    "ru",
    "rw",
    "se",
    "si",
    "sk",
    "sl",
    "sq",
    "sr",
    "sv",
    "sw",
    "ta",
    "te",
    "th",
    "tl",
    "tr",
    "ug",
    "uk",
    "ur",
    "vi",
    "vo",
    "wa",
    "xh",
    "zh",
    "zu",
]
lang_samples = {
    "J'espère que tu vas bien! "
    "Je voulais partager avec toi quelques photos de mon dernier voyage!": "fr",
    "Hola, ¿cómo estás? Espero que estés bien. ¡Hasta pronto!": "es",
    "Hello, how are you? I hope you are well. See you soon!": "en",
    "Hallo, wie geht es dir? Ich hoffe, es geht dir gut. Bis bald!": "de",
    "Ciao, come stai? Spero che tu stia bene. A presto!": "it",
    "Olá, como você está? Espero que você esteja bem. Até logo!": "pt",
    "Привет, как дела? Надеюсь, у тебя все хорошо. Увидимся скоро!": "ru",
    "你好，你好吗？希望你一切都好。很快见到你！": "zh",
    "こんにちは、元気ですか？ あなたが元気であることを願っています。 またね！": "ja",
    "안녕하세요, 어떻게 지내세요? 잘 지내길 바랍니다. 곧 뵙겠습니다!": "ko",
    "مرحبًا، كيف حالك؟ آمل أن تكون بخير. أراك قريبًا!": "ar",
    "नमस्ते, कैसे हो? आशा है कि आप ठीक होंगे। जल्द ही मिलेंगे!": "hi",
}
PUNCTUATIONS_AS_STR = "".join(punctuation)
SINGLE_DETECT_THRESHOLD = 0.7
MULTI_DETECT_THRESHOLD = 0.4
lang_num = 2  # tested up to 3 languages


@pytest.fixture()
def get_lang_detector():
    return utils.LangDetector()


@pytest.fixture()
def get_lang_det_w_init():
    lang_detector = utils.LangDetector()
    lang_detector.init_transformers()
    return lang_detector


@pytest.fixture()
def get_mixed_lang_docs():
    docs = {}
    sentences = list(lang_samples.keys())
    repeat_num = 10
    for i in range(len(sentences) - (lang_num - 1)):
        # create a text with sentences in lang_num different languages,
        # each sentence is repeated repeat_num times before the next sentence is added
        tmp_sentences = []
        tmp_lang = []
        for j in range(lang_num):
            tmp_sentences += [sentences[i + j]] * repeat_num + ["\n"]
            tmp_lang.append(lang_samples[sentences[i + j]])
            repeat_num = max(0, repeat_num - repeat_num // 2)
        text = " ".join(tmp_sentences)
        docs[text] = tmp_lang

    return docs


def test_init_transformers(get_lang_detector):
    get_lang_detector.init_transformers()
    assert get_lang_detector.lang_detector_trans is not None

    # Test with an invalid model
    with pytest.raises(OSError):
        get_lang_detector.init_transformers(model="invalid-model")


def test_contains_only_punctuations(get_lang_detector):
    assert get_lang_detector.contains_only_punctuations(".,;:!?") is True
    assert get_lang_detector.contains_only_punctuations(".,;:!?a") is False
    assert get_lang_detector.contains_only_punctuations(".,;:!? ") is True
    assert get_lang_detector.contains_only_punctuations(".,;:!? a") is False
    assert get_lang_detector.contains_only_punctuations(PUNCTUATIONS_AS_STR) is True
    assert (
        get_lang_detector.contains_only_punctuations(PUNCTUATIONS_AS_STR + "a sentence")
        is False
    )


def test_strip_punctuations(get_lang_detector):
    assert get_lang_detector.strip_punctuations(".,;:!?") == ""
    assert get_lang_detector.strip_punctuations(".,;:!?a") == "a"
    assert get_lang_detector.strip_punctuations(".,;:!? ") == " "
    assert get_lang_detector.strip_punctuations(".,;:!? a") == " a"
    assert get_lang_detector.strip_punctuations(PUNCTUATIONS_AS_STR) == ""
    assert (
        get_lang_detector.strip_punctuations(PUNCTUATIONS_AS_STR + "\n a sentence")
        == "\n a sentence"
    )


def test_contains_only_numbers(get_lang_detector):
    assert get_lang_detector.contains_only_numbers("1234567890") is True
    assert get_lang_detector.contains_only_numbers("1234567890a") is False
    assert get_lang_detector.contains_only_numbers("1234567890 ") is True
    assert get_lang_detector.contains_only_numbers("1234567890 a") is False
    assert (
        get_lang_detector.contains_only_numbers("1234567890" + PUNCTUATIONS_AS_STR)
        is True
    )
    assert (
        get_lang_detector.contains_only_numbers(
            "1234567890" + PUNCTUATIONS_AS_STR + "a sentence"
        )
        is False
    )


def test_contains_only_emails(get_lang_detector):
    assert get_lang_detector.contains_only_emails("abc@gmail.com") is True
    assert get_lang_detector.contains_only_emails("<abc@gmail.com>") is True
    assert (
        get_lang_detector.contains_only_emails("abc@gmail.com \n cdf@gmail.com") is True
    )
    assert get_lang_detector.contains_only_emails("Sent from abc@gmail.com") is False


def test_contains_only_links(get_lang_detector):
    assert get_lang_detector.contains_only_links("http://www.google.com") is True
    assert get_lang_detector.contains_only_links("https://some.link") is True
    assert get_lang_detector.contains_only_links("http://a.b https://a") is True
    assert (
        get_lang_detector.contains_only_links("Sent from http://www.google.com")
        is False
    )


def test_lang_detector(get_lang_detector):
    assert get_lang_detector.lang_id.nb_classes == LANGID_LANGS


def test_constrain_langid(get_lang_detector):
    lang_set = ["es", "fr"]
    get_lang_detector.constrain_langid(lang_set)
    assert get_lang_detector.lang_id.nb_classes == lang_set


def test_constrain_langid_empty(get_lang_detector):
    lang_set = []
    get_lang_detector.constrain_langid(lang_set)
    assert get_lang_detector.lang_id.nb_classes == LANGID_LANGS


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
    for _ in range(10):
        sample_text = list(lang_samples.keys())[0]
        detection = get_lang_detector.detect_with_langdetect(sample_text)
        _, prob = detection[0]
        probs.append(prob)
    assert len(set(probs)) == 1


def test_detect_single_lang_with_transformers(get_lang_det_w_init):
    for sent, lang in lang_samples.items():
        detections = get_lang_det_w_init.detect_with_transformers(sent)
        det_lang, prob = detections[0]
        if lang == "ko":
            # this transformer model does not support detecting Korean
            with pytest.raises(AssertionError):
                assert det_lang == lang
                assert prob > SINGLE_DETECT_THRESHOLD
        else:
            assert det_lang == lang
            assert prob > SINGLE_DETECT_THRESHOLD


def test_detect_single_lang_with_transformers_no_init(get_lang_detector):
    # check that the transformers model is initialized if not explicitly done
    get_lang_detector.detect_with_transformers("This is a test.")
    assert get_lang_detector.lang_detector_trans


def test_detect_singe_lang_with_langid(get_lang_detector):
    for sent, lang in lang_samples.items():
        detection = get_lang_detector.detect_with_langid(sent)
        det_lang, prob = detection[0]
        assert det_lang == lang
        assert prob > SINGLE_DETECT_THRESHOLD


def test_detect_single_lang_with_langid_error(get_lang_detector):
    with pytest.raises(ValueError):
        get_lang_detector.detect_with_langid(None)


def test_detect_single_lang_with_langdetect_error(get_lang_detector):
    with pytest.raises(ValueError):
        get_lang_detector.detect_with_langdetect(None)
    with pytest.raises(ValueError):
        get_lang_detector.detect_with_langdetect("")
    with pytest.raises(ValueError):
        get_lang_detector.detect_with_langdetect(" \n\n")
    with pytest.raises(ValueError):
        get_lang_detector.detect_with_langdetect(".,;:!?")
    with pytest.raises(ValueError):
        get_lang_detector.detect_with_langdetect("1234567890")
    with pytest.raises(ValueError):
        get_lang_detector.detect_with_langdetect("<abc@gmail.com>")


def test_detect_single_lang_with_langdetect(get_lang_detector):
    get_lang_detector.determine_langdetect()
    for sent, lang in lang_samples.items():
        detection = get_lang_detector.detect_with_langdetect(sent)
        det_lang, prob = detection[0]
        # special case of zh with langdetect
        det_lang = "zh" if det_lang == "zh-cn" else det_lang
        det_lang = "zh" if det_lang == "zh-tw" else det_lang
        assert det_lang == lang
        assert prob > SINGLE_DETECT_THRESHOLD


def test_detect_mixed_lang_with_transformers(get_lang_det_w_init, get_mixed_lang_docs):
    for doc in get_mixed_lang_docs:
        detections = get_lang_det_w_init.detect_with_transformers(doc)
        det_lang, prob = detections[0]
        exceptions_two_langs = (lang_num == 2) and get_mixed_lang_docs[doc][0] in [
            "en",
            "it",
            "zh",
            "ko",
            "ar",
        ]
        exceptions_three_langs = (lang_num == 3) and get_mixed_lang_docs[doc][0] in [
            "en",
            "de",
            "it",
            "ru",
            "zh",
            "ko",
        ]
        if exceptions_two_langs or exceptions_three_langs:
            # detected lang is incorrect
            with pytest.raises(AssertionError):
                assert det_lang == get_mixed_lang_docs[doc][0]
                assert prob > MULTI_DETECT_THRESHOLD
        else:
            assert det_lang == get_mixed_lang_docs[doc][0]
            assert prob > MULTI_DETECT_THRESHOLD


def test_detect_mixed_lang_with_langid(get_lang_detector, get_mixed_lang_docs):
    for doc in get_mixed_lang_docs:
        if lang_num > 3:
            continue

        detection = get_lang_detector.detect_with_langid(doc)
        det_lang, prob = detection[0]
        exceptions_two_langs = (lang_num == 2) and get_mixed_lang_docs[doc][0] in [
            "en",
            "it",
            "pt",
            "zh",
            "ar",
        ]
        exceptions_three_langs = (lang_num == 3) and get_mixed_lang_docs[doc][0] in [
            "en",
            "zh",
            "ar",
        ]
        failed_three_langs = (lang_num == 3) and get_mixed_lang_docs[doc][0] in [
            "de",
            "it",
            "pt",
            "ru",
        ]
        if exceptions_two_langs or exceptions_three_langs:
            # detected lang is the second one in the doc
            assert det_lang == get_mixed_lang_docs[doc][1]
            assert prob > MULTI_DETECT_THRESHOLD
        elif failed_three_langs:
            # detected lang is completely wrong
            with pytest.raises(AssertionError):
                assert det_lang == get_mixed_lang_docs[doc][0]
                assert prob > MULTI_DETECT_THRESHOLD
        else:
            assert det_lang == get_mixed_lang_docs[doc][0]
            assert prob > MULTI_DETECT_THRESHOLD


def test_detect_mixed_lang_with_langdetect(get_lang_detector, get_mixed_lang_docs):
    get_lang_detector.determine_langdetect()
    incomplete_detec = []
    for doc in get_mixed_lang_docs:
        if lang_num > 2:
            continue

        detections = get_lang_detector.detect_with_langdetect(doc)
        det_lang1, prob1 = detections[0]
        wrong_detect_first_lang = get_mixed_lang_docs[doc][0] in [
            "de",
            "it",
            "pt",
            "zh",
            "ko",
            "ar",
        ]
        if wrong_detect_first_lang:
            with pytest.raises(AssertionError):
                assert det_lang1 == get_mixed_lang_docs[doc][0]
                assert prob1 > MULTI_DETECT_THRESHOLD
        else:
            assert det_lang1 == get_mixed_lang_docs[doc][0]
            assert prob1 > MULTI_DETECT_THRESHOLD

        wrong_detect_second_lang = len(detections) > 1 and (
            get_mixed_lang_docs[doc][0] in ["en", "pt", "ar"]
        )
        if wrong_detect_second_lang:
            with pytest.raises(AssertionError):
                assert detections[1][0] == get_mixed_lang_docs[doc][1]
                assert detections[1][1] > MULTI_DETECT_THRESHOLD
        elif len(detections) <= 1:
            incomplete_detec.append(doc)
            incomplete_detec.append("\n")
        else:
            assert detections[1][0] == get_mixed_lang_docs[doc][1]
            assert detections[1][1] > MULTI_DETECT_THRESHOLD
    print(" ".join(incomplete_detec))


def test_get_detections(get_lang_det_w_init):
    sentence = list(lang_samples.keys())[0]
    detection_langid = get_lang_det_w_init.get_detections(sentence, "langid")
    detection_langdetect = get_lang_det_w_init.get_detections(sentence, "langdetect")
    detection_trans = get_lang_det_w_init.get_detections(sentence, "trans")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] == detection_trans[0][0]
    assert detection_langid[0][0] == lang_samples[sentence]


def test_get_detections_empty(get_lang_detector):
    sentence = " \n\n"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert math.isclose(detection_langid[0][1], 0.0)
    assert math.isclose(detection_langdetect[0][1], 0.0)


def test_get_detections_only_punctuations(get_lang_detector):
    sentence = ".,;:!?"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert math.isclose(detection_langid[0][1], 0.0)
    assert math.isclose(detection_langdetect[0][1], 0.0)


def test_get_detections_only_numbers(get_lang_detector):
    sentence = "1234567890"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert math.isclose(detection_langid[0][1], 0.0)
    assert math.isclose(detection_langdetect[0][1], 0.0)


def test_get_detections_only_emails(get_lang_detector):
    sentence = "<abc@gmail.com>"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert math.isclose(detection_langid[0][1], 0.0)
    assert math.isclose(detection_langdetect[0][1], 0.0)


def test_get_detections_fail(get_lang_detector):
    sentence = list(lang_samples.keys())[0]
    with pytest.raises(ValueError):
        get_lang_detector.get_detections(sentence, "not_a_lib")


def test_detect_lang_sentences_langid(get_lang_det_w_init, get_mixed_lang_docs):
    for doc in get_mixed_lang_docs:
        sentences = doc.split("\n")
        lang_tree = get_lang_det_w_init.detect_lang_sentences(sentences, "langid")
        assert lang_tree.begin() == 0
        assert lang_tree.end() == len(doc.split("\n"))
        for i, interval in enumerate(sorted(lang_tree.items())):
            detected_lang = interval.data
            assert detected_lang == get_mixed_lang_docs[doc][i]


def test_detect_lang_sentences_langdetect(get_lang_det_w_init, get_mixed_lang_docs):
    for doc in get_mixed_lang_docs:
        sentences = doc.split("\n")
        lang_tree = get_lang_det_w_init.detect_lang_sentences(sentences, "langdetect")
        assert lang_tree.begin() == 0
        assert lang_tree.end() == len(doc.split("\n"))
        for i, interval in enumerate(sorted(lang_tree.items())):
            detected_lang = interval.data.split("-")[0]
            assert detected_lang == get_mixed_lang_docs[doc][i]


def test_detect_lang_sentences_trans(get_lang_det_w_init, get_mixed_lang_docs):
    for doc in get_mixed_lang_docs:
        sentences = doc.split("\n")
        lang_tree = get_lang_det_w_init.detect_lang_sentences(sentences, "trans")
        assert lang_tree.begin() == 0
        assert lang_tree.end() == len(doc.split("\n"))
        for i, interval in enumerate(sorted(lang_tree.items())):
            detected_lang = interval.data
            if get_mixed_lang_docs[doc][i] == "ko":
                # this transformer model does not support detecting Korean
                with pytest.raises(AssertionError):
                    assert detected_lang == get_mixed_lang_docs[doc][i]
            else:
                assert detected_lang == get_mixed_lang_docs[doc][i]

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


@pytest.mark.langdet
def test_init_transformers(get_lang_detector):
    get_lang_detector.init_transformers()
    assert get_lang_detector.lang_detector_trans is not None

    # Test with an invalid model
    with pytest.raises(OSError):
        get_lang_detector.init_transformers(model="invalid-model")


@pytest.mark.langdet
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


@pytest.mark.langdet
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


@pytest.mark.langdet
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


@pytest.mark.langdet
def test_contains_only_emails(get_lang_detector):
    assert get_lang_detector.contains_only_emails("abc@gmail.com") is True
    assert get_lang_detector.contains_only_emails("<abc@gmail.com>") is True
    assert (
        get_lang_detector.contains_only_emails("abc@gmail.com \n cdf@gmail.com") is True
    )
    assert get_lang_detector.contains_only_emails("Sent from abc@gmail.com") is False


@pytest.mark.langdet
def test_contains_only_links(get_lang_detector):
    assert get_lang_detector.contains_only_links("http://www.google.com") is True
    assert get_lang_detector.contains_only_links("https://some.link") is True
    assert get_lang_detector.contains_only_links("http://a.b https://a") is True
    assert (
        get_lang_detector.contains_only_links("Sent from http://www.google.com")
        is False
    )


@pytest.mark.langdet
def test_lang_detector(get_lang_detector):
    assert get_lang_detector.lang_id.nb_classes == LANGID_LANGS


@pytest.mark.langdet
def test_constrain_langid(get_lang_detector):
    lang_set = ["es", "fr"]
    get_lang_detector.constrain_langid(lang_set)
    assert get_lang_detector.lang_id.nb_classes == lang_set


@pytest.mark.langdet
def test_constrain_langid_empty(get_lang_detector):
    lang_set = []
    get_lang_detector.constrain_langid(lang_set)
    assert get_lang_detector.lang_id.nb_classes == LANGID_LANGS


@pytest.mark.langdet
def test_constrain_langid_intersec(get_lang_detector):
    lang_set = ["es", "fr", "not_a_language"]
    get_lang_detector.constrain_langid(lang_set)
    assert get_lang_detector.lang_id.nb_classes == ["es", "fr"]


@pytest.mark.langdet
def test_constrain_langid_fail(get_lang_detector):
    lang_set = ["not_a_language"]
    with pytest.raises(ValueError):
        get_lang_detector.constrain_langid(lang_set)


@pytest.mark.langdet
def test_determine_langdetect(get_lang_detector):
    get_lang_detector.determine_langdetect()
    probs = []
    for _ in range(10):
        sample_text = list(lang_samples.keys())[0]
        detection = get_lang_detector.detect_with_langdetect(sample_text)
        _, prob = detection[0]
        probs.append(prob)
    assert len(set(probs)) == 1


@pytest.mark.langdet
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


@pytest.mark.langdet
def test_detect_single_lang_with_transformers_no_init(get_lang_detector):
    # check that the transformers model is initialized if not explicitly done
    get_lang_detector.detect_with_transformers("This is a test.")
    assert get_lang_detector.lang_detector_trans


@pytest.mark.langdet
def test_detect_singe_lang_with_langid(get_lang_detector):
    for sent, lang in lang_samples.items():
        detection = get_lang_detector.detect_with_langid(sent)
        det_lang, prob = detection[0]
        assert det_lang == lang
        assert prob > SINGLE_DETECT_THRESHOLD


@pytest.mark.langdet
def test_detect_single_lang_with_langid_error(get_lang_detector):
    with pytest.raises(ValueError):
        get_lang_detector.detect_with_langid(None)


@pytest.mark.langdet
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


@pytest.mark.langdet
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


@pytest.mark.langdet
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


@pytest.mark.langdet
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


@pytest.mark.langdet
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


@pytest.mark.langdet
def test_get_detections(get_lang_det_w_init):
    sentence = list(lang_samples.keys())[0]
    detection_langid = get_lang_det_w_init.get_detections(sentence, "langid")
    detection_langdetect = get_lang_det_w_init.get_detections(sentence, "langdetect")
    detection_trans = get_lang_det_w_init.get_detections(sentence, "trans")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] == detection_trans[0][0]
    assert detection_langid[0][0] == lang_samples[sentence]


@pytest.mark.langdet
def test_get_detections_empty(get_lang_detector):
    sentence = " \n\n"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert math.isclose(detection_langid[0][1], 0.0)
    assert math.isclose(detection_langdetect[0][1], 0.0)


@pytest.mark.langdet
def test_get_detections_only_punctuations(get_lang_detector):
    sentence = ".,;:!?"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert math.isclose(detection_langid[0][1], 0.0)
    assert math.isclose(detection_langdetect[0][1], 0.0)


@pytest.mark.langdet
def test_get_detections_only_numbers(get_lang_detector):
    sentence = "1234567890"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert math.isclose(detection_langid[0][1], 0.0)
    assert math.isclose(detection_langdetect[0][1], 0.0)


@pytest.mark.langdet
def test_get_detections_only_emails(get_lang_detector):
    sentence = "<abc@gmail.com>"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert math.isclose(detection_langid[0][1], 0.0)
    assert math.isclose(detection_langdetect[0][1], 0.0)


@pytest.mark.langdet
def test_get_detections_fail(get_lang_detector):
    sentence = list(lang_samples.keys())[0]
    with pytest.raises(ValueError):
        get_lang_detector.get_detections(sentence, "not_a_lib")


@pytest.mark.langdet
def test_detect_lang_sentences_langid(get_lang_det_w_init, get_mixed_lang_docs):
    for doc in get_mixed_lang_docs:
        sentences = doc.split("\n")
        lang_tree = get_lang_det_w_init.detect_lang_sentences(sentences, "langid")
        assert lang_tree.begin() == 0
        assert lang_tree.end() == len(doc.split("\n"))
        for i, interval in enumerate(sorted(lang_tree.items())):
            detected_lang = interval.data
            assert detected_lang == get_mixed_lang_docs[doc][i]


@pytest.mark.langdet
def test_detect_lang_sentences_langdetect(get_lang_det_w_init, get_mixed_lang_docs):
    for doc in get_mixed_lang_docs:
        sentences = doc.split("\n")
        lang_tree = get_lang_det_w_init.detect_lang_sentences(sentences, "langdetect")
        assert lang_tree.begin() == 0
        assert lang_tree.end() == len(doc.split("\n"))
        for i, interval in enumerate(sorted(lang_tree.items())):
            detected_lang = interval.data.split("-")[0]
            assert detected_lang == get_mixed_lang_docs[doc][i]


@pytest.mark.langdet
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


@pytest.fixture()
def get_spacy_loader():
    return utils.SpacyLoader()


def test_init_spacy(get_spacy_loader):
    with pytest.raises(KeyError):
        get_spacy_loader.init_spacy("not_a_language")
    with pytest.raises(SystemExit):
        get_spacy_loader.init_spacy("fr", "not_an_existing_spacy_model")


@pytest.fixture()
def get_time_detector():
    return utils.TimeDetector(lang="fr")


sample_parsed_dates = {
    "absolute": {
        "2025-03-10": datetime.datetime(2025, 3, 10, 0, 0),
        "2025-03-10 12:15:20": datetime.datetime(2025, 3, 10, 12, 15, 20),
        "May 10, 2025": datetime.datetime(2025, 5, 10, 0, 0),
        "15.03.2025": datetime.datetime(2025, 3, 15, 0, 0),
        "10 mars 2025": datetime.datetime(2025, 3, 10, 0, 0),
    },
    "relative": {
        "tomorrow": datetime.date.today() + datetime.timedelta(days=1),
        "today": datetime.date.today(),
        "two weeks ago": datetime.date.today() - datetime.timedelta(days=14),
        "in two weeks": datetime.date.today() + datetime.timedelta(days=14),
        "2 weeks ago": datetime.date.today() - datetime.timedelta(days=14),
        "demain": datetime.date.today() + datetime.timedelta(days=1),
        "aujourd'hui": datetime.date.today(),
        "il y a deux semaines": datetime.date.today() - datetime.timedelta(days=14),
        "dans deux semaines": datetime.date.today() + datetime.timedelta(days=14),
        "il y a 2 semaines": datetime.date.today() - datetime.timedelta(days=14),
    },
    "invalid": ["2025-13-15", "2025-23-17 25:15:20"],
    "confusing": {
        "10.03.2025": datetime.datetime(2025, 10, 3, 0, 0),
        "2025-15-10": datetime.datetime(2025, 10, 15, 0, 0),
    },
}


@pytest.mark.datelib
def test_parse_time(get_time_detector):
    for date_str, date_obj in sample_parsed_dates["absolute"].items():
        assert get_time_detector.parse_time(date_str) == date_obj
    for date_str, date_obj in sample_parsed_dates["relative"].items():
        assert get_time_detector.parse_time(date_str).date() == date_obj
    for date_str in sample_parsed_dates["invalid"]:
        assert get_time_detector.parse_time(date_str) is None
    for date_str, date_obj in sample_parsed_dates["confusing"].items():
        assert get_time_detector.parse_time(date_str) == date_obj


@pytest.mark.datelib
def test_search_dates(get_time_detector):
    extra_info_en = "The date in the email is: "
    extra_info_fr = "La date dans l'e-mail est: "
    for i, data in enumerate(sample_parsed_dates["absolute"].items()):
        date_str, date_obj = data
        if i < 4:
            results = get_time_detector.search_dates(
                extra_info_en + date_str, langs=["en"]
            )
            if date_str not in ["15.03.2025"]:
                assert results[0][0] == date_str
                assert results[0][1] == date_obj
        else:
            results = get_time_detector.search_dates(
                extra_info_fr + date_str, langs=["fr"]
            )
            assert results[0][0] == date_str
            assert results[0][1] == date_obj
    for i, data in enumerate(sample_parsed_dates["relative"].items()):
        date_str, date_obj = data
        if i < 5:
            results = get_time_detector.search_dates(
                extra_info_en + date_str, langs=["en"]
            )
            assert results[0][0] == date_str
            assert results[0][1].date() == date_obj
        else:
            results = get_time_detector.search_dates(
                extra_info_fr + date_str, langs=["fr"]
            )
            if date_str not in ["il y a deux semaines", "il y a 2 semaines"]:
                assert results[0][0] == date_str
                assert results[0][1].date() == date_obj
    for date_str in sample_parsed_dates["invalid"]:
        assert (
            get_time_detector.search_dates(extra_info_en + date_str, langs=["en"])
            == None
        )
    for date_str, date_obj in sample_parsed_dates["confusing"].items():
        if date_str == "10.03.2025":
            with pytest.raises(AssertionError):
                assert get_time_detector.search_dates(
                    extra_info_en + date_str, langs=["en"]
                ) == [(date_str, date_obj)]
        else:
            assert get_time_detector.search_dates(
                extra_info_en + date_str, langs=["en"]
            ) == [(date_str, date_obj)]


@pytest.mark.datelib
def test_find_dates(get_time_detector):
    extra_info = "The date in the email is: "
    for date_str, date_obj in sample_parsed_dates["absolute"].items():
        assert get_time_detector.find_dates(extra_info + date_str) == [date_obj]
    for date_str, date_obj in sample_parsed_dates["relative"].items():
        if date_str not in ["2 weeks ago", "il y a 2 semaines"]:
            assert get_time_detector.find_dates(extra_info + date_str) == []
    for date_str in sample_parsed_dates["invalid"]:
        assert get_time_detector.find_dates(extra_info + date_str) == []
    for date_str, date_obj in sample_parsed_dates["confusing"].items():
        if date_str == "2025-15-10":
            assert get_time_detector.find_dates(extra_info + date_str) == []
        else:
            assert get_time_detector.find_dates(extra_info + date_str) == [date_obj]


@pytest.mark.pattern
def test_add_incorrect_patterns(get_time_detector):
    incorrect_patterns = [
        None,
        [],
        {},
        1,
        "pattern",
        ["pattern"],
        {"pattern": "pattern"},
    ]
    for pattern in incorrect_patterns:
        with pytest.raises(ValueError):
            get_time_detector.add_pattern(pattern)


@pytest.mark.pattern
def test_add_correct_patterns(get_time_detector):
    ogr_len = len(get_time_detector.patterns)
    correct_pattern = [{"POS": "NOUN"}]
    get_time_detector.add_pattern(correct_pattern)
    assert len(get_time_detector.patterns) == ogr_len + 1


@pytest.mark.pattern
def test_add_duplicate_patterns(get_time_detector):
    pattern = get_time_detector.patterns[0]
    with pytest.raises(ValueError):
        get_time_detector.add_pattern(pattern)


@pytest.mark.pattern
def test_remove_existent_patterns(get_time_detector):
    ogr_len = len(get_time_detector.patterns)
    pattern = get_time_detector.patterns[0]
    get_time_detector.remove_pattern(pattern)
    assert len(get_time_detector.patterns) == ogr_len - 1
    assert pattern not in get_time_detector.patterns


@pytest.mark.pattern
def test_remove_non_existent_patterns(get_time_detector):
    non_existent_pattern = [{"POS": "VERB"}, None, []]
    for pattern in non_existent_pattern:
        with pytest.raises(ValueError):
            get_time_detector.remove_pattern(pattern)


sent_fr = "Alice sera présente le {} et apportera 100$."
sample_dates_fr = {
    "absolute": {
        "02/17/2009": {  # NOUN
            "multi": [],
            "single": ["02/17/2009"],
            "total": ["02/17/2009"],
            "detect": ["02/17/2009"],
            "merge": [],
        },
        "17/02/2009": {  # NUM
            "multi": [],
            "single": ["17/02/2009"],
            "total": ["17/02/2009"],
            "detect": ["17/02/2009"],
            "merge": [],
        },
        "2009/02/17": {  # PROPN
            "multi": [],
            "single": ["2009/02/17"],
            "total": ["2009/02/17"],
            "detect": ["2009/02/17"],
            "merge": [],
        },
        "12 mars 2025": {  # NUM -> NOUN -> NUM, nmod
            "multi": ["12 mars 2025"],
            "single": [],
            "total": ["12 mars 2025"],
            "detect": ["12 mars 2025"],
            "merge": [],
        },
        "2/17/2009": {  # PROPN
            "multi": [],
            "single": ["2/17/2009"],
            "total": ["2/17/2009"],
            "detect": ["2/17/2009"],
            "merge": [],
        },
        "17/2/2009": {  # VERB
            "multi": [],
            "single": ["17/2/2009"],
            "total": ["17/2/2009"],
            "detect": ["17/2/2009"],
            "merge": [],
        },
        "2009/2/17": {  # VERB
            "multi": [],
            "single": ["2009/2/17"],
            "total": ["2009/2/17"],
            "detect": ["2009/2/17"],
            "merge": [],
        },
        "09 février 2009": {  # NOUN -> NOUN -> NUM, nmod
            "multi": ["09 février 2009"],
            "single": [],
            "total": ["09 février 2009"],
            "detect": ["09 février 2009"],
            "merge": [],
        },
        "2025-03-12": {  # NOUN-NOUN-NUM
            "multi": ["2025-03-12"],
            "single": [],
            "total": ["2025-03-12"],
            "detect": ["2025-03-12"],
            "merge": [],
        },
        "2025-03-01": {  # NOUN-NOUN-NOUN
            "multi": ["2025-03-01"],
            "single": [],
            "total": ["2025-03-01"],
            "detect": ["2025-03-01"],
            "merge": [],
        },
        "2025-11-20": {  # NOUN-NOUN-NUM
            "multi": ["2025-11-20"],
            "single": [],
            "total": ["2025-11-20"],
            "detect": ["2025-11-20"],
            "merge": [],
        },
        "ven. 14 mars 2025, 10:30": {  # NUM -> NOUN -> NUM, nmod, 10:30 PROPN
            "multi": ["14 mars 2025"],
            "single": ["ven", "10:30"],
            "total": ["ven", "14 mars 2025", "10:30"],
            "detect": ["ven. 14 mars 2025, 10:30"],
            "merge": [(4, 6), (8, 10)],
        },
        "vendredi 14 mars 2025 à 10:30": {  # NUM -> NOUN -> NUM, nmod, 10:30 PROPN
            "multi": ["14 mars 2025"],
            "single": ["vendredi", "10:30"],
            "total": ["vendredi", "14 mars 2025", "10:30"],
            "detect": ["vendredi 14 mars 2025 à 10:30"],
            "merge": [(4, 5), (7, 9)],
        },
        "14/03/2025 10:30": {  # NOUN, 10:30 NOUN
            "multi": [],
            "single": ["14/03/2025", "10:30"],
            "total": ["14/03/2025", "10:30"],
            "detect": ["14/03/2025 10:30"],
            "merge": [(4, 5)],
        },
        "14/03/2025 à 10:30": {  # NOUN, 10:30 PROPN
            "multi": [],
            "single": ["14/03/2025", "10:30"],
            "total": ["14/03/2025", "10:30"],
            "detect": ["14/03/2025 à 10:30"],
            "merge": [(4, 6)],
        },
        "2025-03-14 10:30": {  # NOUN -> NOUN -> NUM, 10:30 PROPN
            "multi": ["2025-03-14"],
            "single": ["10:30"],
            "total": ["2025-03-14", "10:30"],
            "detect": ["2025-03-14 10:30"],
            "merge": [(8, 9)],
        },
        "le 14 mars 2025": {  # NUM -> NOUN -> NUM, nmod
            "multi": ["14 mars 2025"],
            "single": [],
            "total": ["14 mars 2025"],
            "detect": ["14 mars 2025"],
            "merge": [],
        },
        "ce vendredi 14 mars 2025": {  # NUM -> NOUN -> NUM, nmod
            "multi": ["14 mars 2025"],
            "single": ["vendredi"],
            "total": ["vendredi", "14 mars 2025"],
            "detect": ["vendredi 14 mars 2025"],
            "merge": [],
        },
        "2 avril 2015": {  # NUM -> NOUN -> NUM, nmod
            "multi": ["2 avril 2015"],
            "single": [],
            "total": ["2 avril 2015"],
            "detect": ["2 avril 2015"],
            "merge": [],
        },
        "6/12/25": {  # NOUN
            "multi": [],
            "single": ["6/12/25"],
            "total": ["6/12/25"],
            "detect": ["6/12/25"],
            "merge": [],
        },
        "17/04/2024 um 17:23 Uhr": {
            "multi": [],
            "single": ["17/04/2024", "17:23"],
            "total": ["17/04/2024", "17:23"],
            "detect": ["17/04/2024 um 17:23"],
            "merge": [(4, 6)],
        },
        "Mittwoch, 17. April 2024 um 17:23 Uhr": {
            "multi": ["17. April 2024"],
            "single": ["Mittwoch", "17:23"],
            "total": ["Mittwoch", "17. April 2024", "17:23"],
            "detect": ["Mittwoch, 17. April 2024 um 17:23"],
            "merge": [(4, 6), (9, 11)],
        },
        "mié., 17 abr. 2024 17:20:18 +0200": {  # es but it appears in fr emails
            "multi": ["17 abr. 2024"],
            "single": ["mié", "17:20:18", "+0200"],
            "total": ["mié", "17 abr. 2024", "17:20:18", "+0200"],
            "detect": ["mié., 17 abr. 2024 17:20:18 +0200"],
            "merge": [(4, 7), (10, 11), (11, 12)],
        },
        "Wednesday, April 17th 2024 at 17:23": {
            "multi": ["April 17th 2024 at"],
            "single": ["Wednesday", "17:23"],
            "total": ["Wednesday", "April 17th 2024 at", "17:23"],
            "detect": ["Wednesday, April 17th 2024 at 17:23"],
            "merge": [(4, 6), (8, 10)],
        },
    },
    "relative": {},
}
date_type = "absolute"


@pytest.fixture(params=[date for date in sample_dates_fr[date_type]])
def get_date_samples(request):
    return sent_fr.format(request.param), sample_dates_fr[date_type][request.param]


@pytest.mark.pattern
def test_unite_unite_overlapping_words_empty(get_time_detector):
    words, locations = get_time_detector.unite_overlapping_words([], [], None)
    assert words == []
    assert locations == []


@pytest.mark.pattern
def test_unite_unite_overlapping_words_single_item(get_time_detector):
    time_words = [("19/03/2025", None)]
    locations = [(0, 1)]
    updated_words, updated_locations = get_time_detector.unite_overlapping_words(
        time_words, locations, None
    )
    assert updated_words == time_words
    assert updated_locations == locations


@pytest.mark.pattern
def test_unite_unite_overlapping_words_no_overlap(get_time_detector):
    sent = "19/03/2025 something in between 10:30"
    doc = get_time_detector.nlp_spacy(sent)
    time_words = [(doc[0:1], None), (doc[4:5], None)]
    locations = [(0, 1), (4, 5)]
    updated_words, updated_locations = get_time_detector.unite_overlapping_words(
        time_words, locations, None
    )
    assert updated_words == time_words
    assert updated_locations == locations


@pytest.mark.pattern
def test_unite_unite_overlapping_words_overlap_end(get_time_detector):
    sent = "19/03/2025 10:30"
    doc = get_time_detector.nlp_spacy(sent)
    time_words = [(doc[0:1], None), (doc[1:2], None)]
    locations = [(0, 1), (1, 2)]
    updated_words, updated_locations = get_time_detector.unite_overlapping_words(
        time_words, locations, doc
    )
    assert len(updated_words) == 1
    assert updated_words[0][0].text == "19/03/2025 10:30"
    assert updated_locations == [(0, 2)]


@pytest.mark.pattern
def test_unite_overlapping_words_overlap_non_end(get_time_detector):
    sent = "17:13 something 19/03/2025 10:30 something in between 12:30"
    doc = get_time_detector.nlp_spacy(sent)
    time_words = [
        (doc[0:1], None),
        (doc[2:3], None),
        (doc[3:4], None),
        (doc[7:8], None),
    ]
    locations = [(0, 1), (2, 3), (3, 4), (7, 8)]
    updated_words, updated_locations = get_time_detector.unite_overlapping_words(
        time_words, locations, doc
    )
    assert len(updated_words) == 3
    assert updated_words[0][0].text == "17:13"
    assert updated_words[1][0].text == "19/03/2025 10:30"
    assert updated_words[2][0].text == "12:30"
    assert updated_locations == [(0, 1), (2, 4), (7, 8)]


@pytest.mark.pattern
def test_extract_date_time_multi_word_fr(get_time_detector, get_date_samples):
    sample_sentence, date_info = get_date_samples
    doc = get_time_detector.nlp_spacy(sample_sentence)
    multi_word_date_time, marked_locations = (
        get_time_detector.extract_date_time_multi_words(doc)
    )
    assert len(multi_word_date_time) == len(date_info["multi"])
    assert len(marked_locations) == len(date_info["multi"])
    for multi_time, sample_time in zip(multi_word_date_time, date_info["multi"]):
        assert multi_time[0].text == sample_time


@pytest.mark.pattern
def test_extract_date_time_single_word_fr(get_time_detector, get_date_samples):
    sample_sentence, date_info = get_date_samples
    doc = get_time_detector.nlp_spacy(sample_sentence)
    _, marked_locations = get_time_detector.extract_date_time_multi_words(doc)
    word_date_time = get_time_detector.extract_date_time_single_word(
        doc, marked_locations
    )
    assert len(word_date_time) == len(date_info["single"])
    for single_time, sample_time in zip(word_date_time, date_info["single"]):
        assert single_time[0].text == sample_time


@pytest.mark.pattern
def test_get_start_end(get_time_detector, get_date_samples):
    sample_sentence, _ = get_date_samples
    doc = get_time_detector.nlp_spacy(sample_sentence)
    assert get_time_detector._get_start_end(doc[0]) == (0, 0)
    assert get_time_detector._get_start_end(doc[1]) == (1, 1)
    assert get_time_detector._get_start_end(doc[2:7]) == (2, 6)


@pytest.mark.pattern
def test_extract_date_time_fr(get_time_detector, get_date_samples):
    sample_sentence, date_info = get_date_samples
    doc = get_time_detector.nlp_spacy(sample_sentence)
    extracted_date_time = get_time_detector.extract_date_time(doc)
    assert len(extracted_date_time) == len(date_info["total"])
    for e_time, sample_time in zip(extracted_date_time, date_info["total"]):
        assert e_time[0].text == sample_time


@pytest.mark.pattern
def test_get_next_sibling(get_time_detector, get_date_samples):
    sample_sentence, _ = get_date_samples
    doc = get_time_detector.nlp_spacy(sample_sentence)
    token = doc[0]
    assert get_time_detector._get_next_sibling(token) == doc[1]
    assert get_time_detector._get_next_sibling(doc[len(doc) - 1]) == None


@pytest.mark.pattern
def test_is_time_mergeable(get_time_detector, get_date_samples):
    sample_sentence, date_info = get_date_samples
    doc = get_time_detector.nlp_spacy(sample_sentence)
    for s_id, e_id in date_info["merge"]:
        assert get_time_detector.is_time_mergeable(doc[s_id], doc[e_id], doc) == True
    assert get_time_detector.is_time_mergeable(doc[0], doc[7], doc) == False


@pytest.mark.pattern
def test_add_merged_datetime_empty(get_time_detector):
    merged_datetime = []
    new_text = "14/03/2025 à 10:30"
    new_item = (new_text, None, 0, len(new_text))
    get_time_detector.add_merged_datetime(merged_datetime, new_item)
    assert len(merged_datetime) == 1
    assert merged_datetime[0][0] == new_text
    assert merged_datetime[0][1] is None
    assert merged_datetime[0][2] == 0
    assert merged_datetime[0][3] == len(new_text)


@pytest.mark.pattern
def test_add_merged_datetime_non_overlapping(get_time_detector):
    merged_datetime = [("14/03/2025 à 10:30", None, 0, 18)]
    new_text = "17:23"
    new_item = (new_text, None, 18, 18 + len(new_text))
    get_time_detector.add_merged_datetime(merged_datetime, new_item)
    assert len(merged_datetime) == 2
    assert merged_datetime[1][0] == new_text
    assert merged_datetime[1][1] is None
    assert merged_datetime[1][2] == 18
    assert merged_datetime[1][3] == 18 + len(new_text)


@pytest.mark.pattern
def test_add_merged_datetime_overlapping(get_time_detector):
    merged_datetime = [("14/03/2025", None, 0, 11)]
    new_text = "14/03/2025 à 10:30"
    new_item = (new_text, None, 0, len(new_text))
    get_time_detector.add_merged_datetime(merged_datetime, new_item)
    assert len(merged_datetime) == 1
    assert merged_datetime[0][0] == "14/03/2025 à 10:30"
    assert merged_datetime[0][1] is None
    assert merged_datetime[0][2] == 0
    assert merged_datetime[0][3] == len(new_text)


@pytest.mark.pattern
def test_merge_date_time_fr(get_time_detector, get_date_samples):
    sample_sentence, date_info = get_date_samples
    doc = get_time_detector.nlp_spacy(sample_sentence)
    extracted_date_time = get_time_detector.extract_date_time(doc)
    merged_date_time = get_time_detector.merge_date_time(extracted_date_time, doc)
    assert len(merged_date_time) == len(date_info["detect"])
    for m_time, sample_time in zip(merged_date_time, date_info["detect"]):
        assert m_time[0] == sample_time


@pytest.mark.pattern
def test_merg_date_time_empty(get_time_detector):
    doc = get_time_detector.nlp_spacy("Alice")
    extracted_date_time = get_time_detector.extract_date_time(doc)
    merged_date_time = get_time_detector.merge_date_time(extracted_date_time, doc)
    assert len(merged_date_time) == 0


@pytest.mark.pattern
def test_merge_date_time_one_item(get_time_detector):
    doc = get_time_detector.nlp_spacy("14 mars 2025")
    extracted_date_time = get_time_detector.extract_date_time(doc)
    merged_date_time = get_time_detector.merge_date_time(extracted_date_time, doc)
    assert len(merged_date_time) == 1
    assert merged_date_time[0][0] == "14 mars 2025"
    assert merged_date_time[0][2] == 0
    assert merged_date_time[0][3] == 12


@pytest.mark.pattern
def test_get_date_time_fr(get_time_detector, get_date_samples):
    sample_sentence, date_info = get_date_samples
    results = get_time_detector.get_date_time(
        sample_sentence, lang=get_time_detector.lang
    )
    assert len(results) == len(date_info["detect"])
    for result, sample_time in zip(results, date_info["detect"]):
        assert result[0] == sample_time

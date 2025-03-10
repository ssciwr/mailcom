from mailcom import utils
import pytest
from string import punctuation


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


# test cases for email language detection
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
lang_samples = {
    "J'espère que tu vas bien! Je voulais partager avec toi quelques photos de mon dernier voyage!": "fr",
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
punctuations_as_str = "".join(punctuation)
single_detect_threshold = 0.7
multi_detect_threshold = 0.4
repeat_num = 5
lang_num = 2 # tested up to 3 languages


@pytest.fixture()
def get_lang_detector():
    return utils.LangDetector()


@pytest.fixture()
def get_mixed_lang_docs():
    docs = {}
    sentences = list(lang_samples.keys())
    for i in range(len(sentences)-(lang_num-1)):
        # create a text with sentences in lang_num different languages,
        # each sentence is repeated repeat_num times before the next sentence is added
        tmp_sentences = []
        tmp_lang = []
        for j in range(lang_num):
            tmp_sentences += [sentences[i+j]] * repeat_num + ["\n"]
            tmp_lang.append(lang_samples[sentences[i+j]])
        text = " ".join(tmp_sentences)
        docs[text] = tmp_lang

    return docs


def test_contains_only_punctuations(get_lang_detector):
    assert get_lang_detector.contains_only_punctuations(".,;:!?") is True
    assert get_lang_detector.contains_only_punctuations(".,;:!?a") is False
    assert get_lang_detector.contains_only_punctuations(".,;:!? ") is True
    assert get_lang_detector.contains_only_punctuations(".,;:!? a") is False
    assert get_lang_detector.contains_only_punctuations(punctuations_as_str) is True
    assert get_lang_detector.contains_only_punctuations(punctuations_as_str + "a sentence") is False


def test_strip_punctuations(get_lang_detector):
    assert get_lang_detector.strip_punctuations(".,;:!?") == ""
    assert get_lang_detector.strip_punctuations(".,;:!?a") == "a"
    assert get_lang_detector.strip_punctuations(".,;:!? ") == " "
    assert get_lang_detector.strip_punctuations(".,;:!? a") == " a"
    assert get_lang_detector.strip_punctuations(punctuations_as_str) == ""
    assert get_lang_detector.strip_punctuations(punctuations_as_str + "\n a sentence") == "\n a sentence"


def test_contains_only_numbers(get_lang_detector):
    assert get_lang_detector.contains_only_numbers("1234567890") is True
    assert get_lang_detector.contains_only_numbers("1234567890a") is False
    assert get_lang_detector.contains_only_numbers("1234567890 ") is True
    assert get_lang_detector.contains_only_numbers("1234567890 a") is False
    assert get_lang_detector.contains_only_numbers("1234567890" + punctuations_as_str) is True
    assert get_lang_detector.contains_only_numbers("1234567890" + punctuations_as_str + "a sentence") is False


def test_contains_only_emails(get_lang_detector):
    assert get_lang_detector.contains_only_emails("abc@gmail.com") is True
    assert get_lang_detector.contains_only_emails("<abc@gmail.com>") is True
    assert get_lang_detector.contains_only_emails("abc@gmail.com \n cdf@gmail.com") is True
    assert get_lang_detector.contains_only_emails("Sent from abc@gmail.com") is False


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
        detection = get_lang_detector.detect_with_langdetect(list(lang_samples.keys())[0])
        _, prob = detection[0]
        probs.append(prob)
    assert len(set(probs)) == 1


def test_detect_singe_lang_with_langid(get_lang_detector):
    for sent, lang in lang_samples.items():
        detection = get_lang_detector.detect_with_langid(sent)
        det_lang, prob = detection[0]
        assert det_lang == lang
        assert prob > single_detect_threshold


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
        assert prob > single_detect_threshold


def test_detect_mixed_lang_with_langid(get_lang_detector, get_mixed_lang_docs):
    for doc in get_mixed_lang_docs:
        detection = get_lang_detector.detect_with_langid(doc)
        det_lang, prob = detection[0]
        if (lang_num == 2) and get_mixed_lang_docs[doc][0] in ["en", "it", "pt", "zh", "ar"]:
            # detected lang is the second one in the doc
            assert det_lang == get_mixed_lang_docs[doc][1]
            assert prob > multi_detect_threshold
        elif (lang_num == 3) and get_mixed_lang_docs[doc][0] in ["en", "zh", "ar"]:
            # detected lang is the second one in the doc
            assert det_lang == get_mixed_lang_docs[doc][1]
            assert prob > multi_detect_threshold
        elif (lang_num == 3) and get_mixed_lang_docs[doc][0] in ["de", "it", "pt", "ru"]:
            # detected lang is completely wrong
            with pytest.raises(AssertionError):
                assert det_lang == get_mixed_lang_docs[doc][0]
                assert prob > multi_detect_threshold
        elif lang_num > 3:
            # not tested for more than 3 languages
            pass
        else:
            assert det_lang == get_mixed_lang_docs[doc][0]
            assert prob > multi_detect_threshold


def test_detect_mixed_lang_with_langdetect(get_lang_detector, get_mixed_lang_docs):
    get_lang_detector.determine_langdetect()
    if lang_num == 2:
        incomplete_detec = []
        for doc in get_mixed_lang_docs:
            detections = get_lang_detector.detect_with_langdetect(doc)
            det_lang1, prob1 = detections[0]
            if get_mixed_lang_docs[doc][0] in ["de", "it", "pt", "zh", "ko", "ar"]:
                # detected lang is wrong
                with pytest.raises(AssertionError):
                    assert det_lang1 == get_mixed_lang_docs[doc][0]
                    assert prob1 > multi_detect_threshold
            else:
                assert det_lang1 == get_mixed_lang_docs[doc][0]
                assert prob1 > multi_detect_threshold
            if len(detections) > 1:
                det_lang2, prob2 = detections[1]
                if get_mixed_lang_docs[doc][0] in ["en", "pt", "ar"]:
                    # detected lang is completely wrong
                    with pytest.raises(AssertionError):
                        assert det_lang2 == get_mixed_lang_docs[doc][1]
                        assert prob2 > multi_detect_threshold
                else:
                    assert det_lang2 == get_mixed_lang_docs[doc][1]
            else:
                incomplete_detec.append(doc)
                incomplete_detec.append("\n")
        print(" ".join(incomplete_detec))


def test_get_detections(get_lang_detector):
    sentence = list(lang_samples.keys())[0]
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] == lang_samples[sentence]


def test_get_detections_empty(get_lang_detector):
    sentence = " \n\n"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert detection_langid[0][1] == 0.0
    assert detection_langdetect[0][1] == 0.0


def test_get_detections_only_punctuations(get_lang_detector):
    sentence = ".,;:!?"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert detection_langid[0][1] == 0.0
    assert detection_langdetect[0][1] == 0.0


def test_get_detections_only_numbers(get_lang_detector):
    sentence = "1234567890"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert detection_langid[0][1] == 0.0
    assert detection_langdetect[0][1] == 0.0


def test_get_detections_only_emails(get_lang_detector):
    sentence = "<abc@gmail.com>"
    detection_langid = get_lang_detector.get_detections(sentence, "langid")
    detection_langdetect = get_lang_detector.get_detections(sentence, "langdetect")
    assert detection_langid[0][0] == detection_langdetect[0][0]
    assert detection_langid[0][0] is None
    assert detection_langid[0][1] == 0.0
    assert detection_langdetect[0][1] == 0.0


def test_get_detections_fail(get_lang_detector):
    sentence = list(lang_samples.keys())[0]
    with pytest.raises(ValueError):
        get_lang_detector.get_detections(sentence, "not_a_lib")


def test_detect_lang_sentences(get_lang_detector, get_mixed_lang_docs):
    for lang_lib in ["langid", "langdetect"]:
        for doc in get_mixed_lang_docs:
            sentences = doc.split("\n")
            lang_tree = get_lang_detector.detect_lang_sentences(sentences, lang_lib)
            assert lang_tree.begin() == 0
            assert lang_tree.end() == len(doc.split("\n"))
            for i, interval in enumerate(sorted(lang_tree.items())):
                detected_lang = interval.data.split("-")[0] if lang_lib == "langdetect" else interval.data
                assert detected_lang == get_mixed_lang_docs[doc][i]
from mailcom import utils
import pytest
import datetime


@pytest.fixture()
def get_time_detector():
    return utils.TimeDetector()


sample_dates = {
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


date_samples_fr = {
    "absolute": [
        "02/17/2009",  # NOUN
        "17/02/2009",  # NUM
        "2009/02/17",  # PROPN
        "12 mars 2025",  # NUM -> NOUN -> NUM, nmod
        "2/17/2009",  # PROPN
        "17/2/2009",  # VERB
        "2009/2/17",  # VERB
        "09 février 2009",  # NOUN -> NOUN -> NUM, nmod
        "2025-03-12",  # NOUN -> NOUN -> NUM
        "ven. 14 mars 2025, 10:30",  # NUM -> NOUN -> NUM, nmod, 10:30 PROPN
        "vendredi 14 mars 2025 à 10:30",  # NUM -> NOUN -> NUM, nmod, 10:30 PROPN
        "14/03/2025 10:30",  # NOUN, 10:30 NOUN
        "14/03/2025 à 10:30",  # NOUN, 10:30 PROPN
        "2025-03-14 10:30",  # NOUN -> NOUN -> NUM, 10:30 PROPN
        "le 14 mars 2025",  # NUM -> NOUN -> NUM, nmod
        "ce vendredi 14 mars 2025",  # NUM -> NOUN -> NUM, nmod
        "2 avril 2015",  # NUM -> NOUN -> NUM, nmod
        "6/12/25",  # NOUN
        "17/04/2024 um 17:23 Uhr",
        "Mittwoch, 17. April 2024 um 17:23 Uhr",
        "mié., 17 abr. 2024 17:20:18 +0200",  # es but it appears in fr emails
    ]
}
sent_fr = "Alice sera présente le {} et apportera 100$."
another_sent_fr = "Alice est arrivée hier à 10:00 AM."


def get_sample_sentences(idx):
    return sent_fr.format(date_samples_fr["absolute"][idx])


def test_parse_time(get_time_detector):
    for date_str, date_obj in sample_dates["absolute"].items():
        assert get_time_detector.parse_time(date_str) == date_obj
    for date_str, date_obj in sample_dates["relative"].items():
        assert get_time_detector.parse_time(date_str).date() == date_obj
    for date_str in sample_dates["invalid"]:
        assert get_time_detector.parse_time(date_str) is None
    for date_str, date_obj in sample_dates["confusing"].items():
        assert get_time_detector.parse_time(date_str) == date_obj


def test_search_dates(get_time_detector):
    extra_info_en = "The date in the email is: "
    extra_info_fr = "La date dans l'e-mail est: "
    for i, data in enumerate(sample_dates["absolute"].items()):
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
    for i, data in enumerate(sample_dates["relative"].items()):
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
    for date_str in sample_dates["invalid"]:
        assert (
            get_time_detector.search_dates(extra_info_en + date_str, langs=["en"])
            == None
        )
    for date_str, date_obj in sample_dates["confusing"].items():
        if date_str == "10.03.2025":
            with pytest.raises(AssertionError):
                assert get_time_detector.search_dates(
                    extra_info_en + date_str, langs=["en"]
                ) == [(date_str, date_obj)]
        else:
            assert get_time_detector.search_dates(
                extra_info_en + date_str, langs=["en"]
            ) == [(date_str, date_obj)]


def test_find_dates(get_time_detector):
    extra_info = "The date in the email is: "
    for date_str, date_obj in sample_dates["absolute"].items():
        assert get_time_detector.find_dates(extra_info + date_str) == [date_obj]
    for date_str, date_obj in sample_dates["relative"].items():
        if date_str not in ["2 weeks ago", "il y a 2 semaines"]:
            assert get_time_detector.find_dates(extra_info + date_str) == []
    for date_str in sample_dates["invalid"]:
        assert get_time_detector.find_dates(extra_info + date_str) == []
    for date_str, date_obj in sample_dates["confusing"].items():
        if date_str == "2025-15-10":
            assert get_time_detector.find_dates(extra_info + date_str) == []
        else:
            assert get_time_detector.find_dates(extra_info + date_str) == [date_obj]


def test_extract_date_time_multi_word_fr(get_time_detector):
    sample_sentence = get_sample_sentences(19)
    get_time_detector.parse.init_spacy("fr")
    doc = get_time_detector.parse.nlp_spacy(sample_sentence)
    multi_word_date_time, marked_locations = (
        get_time_detector.extract_date_time_multi_words(doc)
    )
    assert len(multi_word_date_time) == 1
    assert len(marked_locations) == 1
    assert multi_word_date_time[0][0].text == "17. April 2024"


def test_extract_date_time_single_word_fr(get_time_detector):
    sample_sentence = get_sample_sentences(19)
    get_time_detector.parse.init_spacy("fr")
    doc = get_time_detector.parse.nlp_spacy(sample_sentence)
    _, marked_locations = get_time_detector.extract_date_time_multi_words(doc)
    word_date_time = get_time_detector.extract_date_time_single_word(
        doc, marked_locations
    )
    assert len(word_date_time) == 2
    assert word_date_time[0][0].text == "Mittwoch"
    assert word_date_time[1][0].text == "17:23"
    assert word_date_time[1][1].date() == datetime.date.today()
    assert word_date_time[1][1].time() == datetime.time(17, 23)


def test_get_start_end(get_time_detector):
    sample_sentence = get_sample_sentences(19)
    get_time_detector.parse.init_spacy("fr")
    doc = get_time_detector.parse.nlp_spacy(sample_sentence)
    assert get_time_detector._get_start_end(doc[0]) == (0, 0)
    assert get_time_detector._get_start_end(doc[1]) == (1, 1)
    assert get_time_detector._get_start_end(doc[2:7]) == (2, 6)


def test_extract_date_time_fr(get_time_detector):
    sample_sentence = get_sample_sentences(19)
    get_time_detector.parse.init_spacy("fr")
    doc = get_time_detector.parse.nlp_spacy(sample_sentence)
    extracted_date_time = get_time_detector.extract_date_time(doc)
    assert len(extracted_date_time) == 3
    assert extracted_date_time[0][0].text == "Mittwoch"
    assert extracted_date_time[1][0].text == "17. April 2024"
    assert extracted_date_time[1][1] == datetime.datetime(2024, 4, 17, 0, 0)
    assert extracted_date_time[2][0].text == "17:23"
    assert extracted_date_time[2][1].date() == datetime.date.today()
    assert extracted_date_time[2][1].time() == datetime.time(17, 23)


def test_get_next_sibling(get_time_detector):
    sample_sentence = get_sample_sentences(12)
    get_time_detector.parse.init_spacy("fr")
    doc = get_time_detector.parse.nlp_spacy(sample_sentence)
    token = doc[6]
    assert get_time_detector._get_next_sibling(token) == doc[8]
    assert get_time_detector._get_next_sibling(doc[len(doc) - 1]) == None


def test_is_time_mergeable(get_time_detector):
    sample_sentence = get_sample_sentences(12)
    get_time_detector.parse.init_spacy("fr")
    doc = get_time_detector.parse.nlp_spacy(sample_sentence)
    assert get_time_detector.is_time_mergeable(doc[4], doc[6], doc) == True
    assert get_time_detector.is_time_mergeable(doc[6], doc[8], doc) == False


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


def test_merge_date_time_fr(get_time_detector):
    sample_sentence = get_sample_sentences(12)
    get_time_detector.parse.init_spacy("fr")
    doc = get_time_detector.parse.nlp_spacy(sample_sentence)
    extracted_date_time = get_time_detector.extract_date_time(doc)
    merged_date_time = get_time_detector.merge_date_time(extracted_date_time, doc)
    assert len(merged_date_time) == 1
    assert merged_date_time[0][0] == "14/03/2025 à 10:30"
    assert merged_date_time[0][1] == datetime.datetime(2025, 3, 14, 10, 30)


def test_get_date_time_fr(get_time_detector):
    sample_sentence = get_sample_sentences(19)
    results = get_time_detector.get_date_time(sample_sentence, lang="fr")
    assert len(results) == 1
    assert results[0][0] == "Mittwoch, 17. April 2024 um 17:23"
    assert results[0][1] == datetime.datetime(2024, 4, 17, 17, 23)

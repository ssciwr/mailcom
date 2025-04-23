import pytest
from mailcom.time_detector import TimeDetector
import datetime
from mailcom.utils import SpacyLoader, get_spacy_instance


@pytest.fixture()
def get_time_detector():
    spacy_loader = SpacyLoader()
    return TimeDetector(spacy_loader=spacy_loader)


@pytest.fixture()
def get_time_detector_w_spacy():
    spacy_loader = SpacyLoader()
    inst = TimeDetector(spacy_loader=spacy_loader)
    inst.nlp_spacy = get_spacy_instance(inst.spacy_loader, "fr")
    return inst


@pytest.fixture()
def get_time_detector_strict():
    spacy_loader = SpacyLoader()
    return TimeDetector(strict_parsing="strict", spacy_loader=spacy_loader)


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
    "incomplete": ["18", "Mittwoch", "2025", "10:30"],
}


@pytest.mark.datelib
def test_parse_time_non_strict(get_time_detector):
    for date_str, date_obj in sample_parsed_dates["absolute"].items():
        assert get_time_detector.parse_time(date_str) == date_obj
    for date_str, date_obj in sample_parsed_dates["relative"].items():
        assert get_time_detector.parse_time(date_str).date() == date_obj
    for date_str in sample_parsed_dates["invalid"]:
        assert get_time_detector.parse_time(date_str) is None
    for date_str, date_obj in sample_parsed_dates["confusing"].items():
        assert get_time_detector.parse_time(date_str) == date_obj
    for date_str in sample_parsed_dates["incomplete"]:
        assert get_time_detector.parse_time(date_str) is not None


@pytest.mark.datelib
def test_parse_time_strict(get_time_detector_strict):
    for date_str, date_obj in sample_parsed_dates["absolute"].items():
        assert get_time_detector_strict.parse_time(date_str) == date_obj
    for date_str, date_obj in sample_parsed_dates["relative"].items():
        assert get_time_detector_strict.parse_time(date_str).date() == date_obj
    for date_str in sample_parsed_dates["invalid"]:
        assert get_time_detector_strict.parse_time(date_str) is None
    for date_str, date_obj in sample_parsed_dates["confusing"].items():
        assert get_time_detector_strict.parse_time(date_str) == date_obj
    for date_str in sample_parsed_dates["incomplete"]:
        assert get_time_detector_strict.parse_time(date_str) is None


@pytest.mark.datelib
def test_search_dates_en(get_time_detector):
    extra_info_en = "The date in the email is: "
    for data in list(sample_parsed_dates["absolute"].items())[:4]:
        date_str, date_obj = data
        results = get_time_detector.search_dates(extra_info_en + date_str, langs=["en"])
        if date_str != "15.03.2025":
            assert results[0][0] == date_str
            assert results[0][1] == date_obj
    for data in list(sample_parsed_dates["relative"].items())[:5]:
        date_str, date_obj = data
        results = get_time_detector.search_dates(extra_info_en + date_str, langs=["en"])
        assert results[0][0] == date_str
        assert results[0][1].date() == date_obj
    for date_str in sample_parsed_dates["invalid"]:
        assert (
            get_time_detector.search_dates(extra_info_en + date_str, langs=["en"])
            is None
        )
    for date_str, date_obj in sample_parsed_dates["confusing"].items():
        if date_str != "10.03.2025":
            assert get_time_detector.search_dates(
                extra_info_en + date_str, langs=["en"]
            ) == [(date_str, date_obj)]


@pytest.mark.datelib
def test_search_dates_fr(get_time_detector):
    extra_info_fr = "La date dans l'e-mail est: "
    for data in list(sample_parsed_dates["absolute"].items())[4:]:
        date_str, date_obj = data
        results = get_time_detector.search_dates(extra_info_fr + date_str, langs=["fr"])
        assert results[0][0] == date_str
        assert results[0][1] == date_obj
    for data in list(sample_parsed_dates["relative"].items())[5:]:
        date_str, date_obj = data
        results = get_time_detector.search_dates(extra_info_fr + date_str, langs=["fr"])
        if date_str not in ["il y a deux semaines", "il y a 2 semaines"]:
            assert results[0][0] == date_str
            assert results[0][1].date() == date_obj


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


@pytest.mark.strict
def test_init_strict_patterns(get_time_detector_strict):
    num_non_strict_patterns = len(get_time_detector_strict.patterns["non-strict"])
    assert "strict" not in get_time_detector_strict.patterns
    get_time_detector_strict.init_strict_patterns()
    assert "strict" in get_time_detector_strict.patterns
    assert len(
        get_time_detector_strict.patterns["strict"]
    ) == num_non_strict_patterns + len(get_time_detector_strict.special_strict_patterns)
    for p_n, p_s in zip(
        get_time_detector_strict.patterns["non-strict"],
        get_time_detector_strict.patterns["strict"][0:num_non_strict_patterns],
    ):
        assert len(p_s) == len(p_n) + 3  # 3 pos for separators (2) and time (1)


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
            get_time_detector.add_pattern(pattern, "non-strict")


@pytest.mark.pattern
def test_add_correct_patterns(get_time_detector):
    mode = "non-strict"
    ogr_len = len(get_time_detector.patterns[mode])
    correct_pattern = [{"POS": "NOUN"}]
    get_time_detector.add_pattern(correct_pattern, mode)
    assert len(get_time_detector.patterns[mode]) == ogr_len + 1


@pytest.mark.pattern
def test_add_duplicate_patterns(get_time_detector):
    mode = "non-strict"
    pattern = get_time_detector.patterns[mode][0]
    with pytest.raises(ValueError):
        get_time_detector.add_pattern(pattern, mode)


@pytest.mark.pattern
def test_remove_existent_patterns(get_time_detector):
    mode = "non-strict"
    ogr_len = len(get_time_detector.patterns[mode])
    pattern = get_time_detector.patterns[mode][0]
    get_time_detector.remove_pattern(pattern, mode)
    assert len(get_time_detector.patterns[mode]) == ogr_len - 1
    assert pattern not in get_time_detector.patterns[mode]


@pytest.mark.pattern
def test_remove_non_existent_patterns(get_time_detector):
    non_existent_pattern = [{"POS": "VERB"}, None, []]
    for pattern in non_existent_pattern:
        with pytest.raises(ValueError):
            get_time_detector.remove_pattern(pattern, "non-strict")


sent_fr = "Alice sera présente le {} et apportera 100$."
sample_dates_fr = {
    "absolute": {
        "02/17/2009": {  # NOUN
            "multi": [],
            "single": ["02/17/2009"],
            "total": ["02/17/2009"],
            "detect": ["02/17/2009"],
            "merge": [],
            "strict": [],
        },
        "17/02/2009": {  # NUM
            "multi": [],
            "single": ["17/02/2009"],
            "total": ["17/02/2009"],
            "detect": ["17/02/2009"],
            "merge": [],
            "strict": [],
        },
        "2009/02/17": {  # PROPN
            "multi": [],
            "single": ["2009/02/17"],
            "total": ["2009/02/17"],
            "detect": ["2009/02/17"],
            "merge": [],
            "strict": [],
        },
        "12 mars 2025": {  # NUM -> NOUN -> NUM, nmod
            "multi": ["12 mars 2025"],
            "single": [],
            "total": ["12 mars 2025"],
            "detect": ["12 mars 2025"],
            "merge": [],
            "strict": [],
        },
        "2/17/2009": {  # PROPN
            "multi": [],
            "single": ["2/17/2009"],
            "total": ["2/17/2009"],
            "detect": ["2/17/2009"],
            "merge": [],
            "strict": [],
        },
        "17/2/2009": {  # VERB
            "multi": [],
            "single": ["17/2/2009"],
            "total": ["17/2/2009"],
            "detect": ["17/2/2009"],
            "merge": [],
            "strict": [],
        },
        "2009/2/17": {  # VERB
            "multi": [],
            "single": ["2009/2/17"],
            "total": ["2009/2/17"],
            "detect": ["2009/2/17"],
            "merge": [],
            "strict": [],
        },
        "09 février 2009": {  # NOUN -> NOUN -> NUM, nmod
            "multi": ["09 février 2009"],
            "single": [],
            "total": ["09 février 2009"],
            "detect": ["09 février 2009"],
            "merge": [],
            "strict": [],
        },
        "2025-03-12": {  # NOUN-NOUN-NUM
            "multi": ["2025-03-12"],
            "single": [],
            "total": ["2025-03-12"],
            "detect": ["2025-03-12"],
            "merge": [],
            "strict": [],
        },
        "2025-03-01": {  # NOUN-NOUN-NOUN
            "multi": ["2025-03-01"],
            "single": [],
            "total": ["2025-03-01"],
            "detect": ["2025-03-01"],
            "merge": [],
            "strict": [],
        },
        "2025-11-20": {  # NOUN-NOUN-NUM
            "multi": ["2025-11-20"],
            "single": [],
            "total": ["2025-11-20"],
            "detect": ["2025-11-20"],
            "merge": [],
            "strict": [],
        },
        "ven. 14 mars 2025, 10:30": {  # NUM -> NOUN -> NUM, nmod, 10:30 PROPN
            "multi": ["14 mars 2025"],
            "single": ["ven", "10:30"],
            "total": ["ven", "14 mars 2025", "10:30"],
            "detect": ["ven. 14 mars 2025, 10:30"],
            "merge": [(4, 6), (8, 10)],
            "strict": ["14 mars 2025, 10:30"],
        },
        "vendredi 14 mars 2025 à 10:30": {  # NUM -> NOUN -> NUM, nmod, 10:30 PROPN
            "multi": ["14 mars 2025"],
            "single": ["vendredi", "10:30"],
            "total": ["vendredi", "14 mars 2025", "10:30"],
            "detect": ["vendredi 14 mars 2025 à 10:30"],
            "merge": [(4, 5), (7, 9)],
            "strict": ["14 mars 2025 à 10:30"],
        },
        "14/03/2025 10:30": {  # NOUN, 10:30 NOUN
            "multi": [],
            "single": ["14/03/2025", "10:30"],
            "total": ["14/03/2025", "10:30"],
            "detect": ["14/03/2025 10:30"],
            "merge": [(4, 5)],
            "strict": ["14/03/2025 10:30"],  # 14/03/2025 is one word
        },
        "14/03/2025 à 10:30": {  # NOUN, 10:30 PROPN
            "multi": [],
            "single": ["14/03/2025", "10:30"],
            "total": ["14/03/2025", "10:30"],
            "detect": ["14/03/2025 à 10:30"],
            "merge": [(4, 6)],
            "strict": ["14/03/2025 à 10:30"],  # 14/03/2025 is one word
        },
        "2025-03-14 10:30": {  # NOUN -> NOUN -> NUM, 10:30 PROPN
            "multi": ["2025-03-14"],
            "single": ["10:30"],
            "total": ["2025-03-14", "10:30"],
            "detect": ["2025-03-14 10:30"],
            "merge": [(8, 9)],
            "strict": ["2025-03-14 10:30"],
        },
        "le 14 mars 2025": {  # NUM -> NOUN -> NUM, nmod
            "multi": ["14 mars 2025"],
            "single": [],
            "total": ["14 mars 2025"],
            "detect": ["14 mars 2025"],
            "merge": [],
            "strict": [],
        },
        "ce vendredi 14 mars 2025": {  # NUM -> NOUN -> NUM, nmod
            "multi": ["14 mars 2025"],
            "single": ["vendredi"],
            "total": ["vendredi", "14 mars 2025"],
            "detect": ["vendredi 14 mars 2025"],
            "merge": [],
            "strict": [],
        },
        "2 avril 2015": {  # NUM -> NOUN -> NUM, nmod
            "multi": ["2 avril 2015"],
            "single": [],
            "total": ["2 avril 2015"],
            "detect": ["2 avril 2015"],
            "merge": [],
            "strict": [],
        },
        "6/12/25": {  # NOUN
            "multi": [],
            "single": ["6/12/25"],
            "total": ["6/12/25"],
            "detect": ["6/12/25"],
            "merge": [],
            "strict": [],
        },
        "17/04/2024 um 17:23 Uhr": {
            "multi": [],
            "single": ["17/04/2024", "17:23"],
            "total": ["17/04/2024", "17:23"],
            "detect": ["17/04/2024 um 17:23"],
            "merge": [(4, 6)],
            "strict": ["17/04/2024 um 17:23"],  # 17/04/2024 is one word
        },
        "Mittwoch, 17. April 2024 um 17:23 Uhr": {
            "multi": ["17. April 2024"],
            "single": ["Mittwoch", "17:23"],
            "total": ["Mittwoch", "17. April 2024", "17:23"],
            "detect": ["Mittwoch, 17. April 2024 um 17:23"],
            "merge": [(4, 6), (9, 11)],
            "strict": ["17. April 2024 um 17:23"],
        },
        "mié., 17 abr. 2024 17:20:18 +0200": {  # es but it appears in fr emails
            "multi": ["17 abr. 2024"],
            "single": ["mié", "17:20:18", "+0200"],
            "total": ["mié", "17 abr. 2024", "17:20:18", "+0200"],
            "detect": ["mié., 17 abr. 2024 17:20:18 +0200"],
            "merge": [(4, 7), (10, 11), (11, 12)],
            "strict": ["17 abr. 2024 17:20:18 +0200"],
        },
        "Wednesday, April 17th 2024 at 17:23": {
            "multi": ["April 17th 2024 at"],
            "single": ["Wednesday", "17:23"],
            "total": ["Wednesday", "April 17th 2024 at", "17:23"],
            "detect": ["Wednesday, April 17th 2024 at 17:23"],
            "merge": [(4, 6), (8, 10)],
            "strict": ["April 17th 2024 at 17:23"],
        },
        "el 24 a las 3": {
            "multi": [],
            "single": ["24", "3"],
            "total": ["24", "3"],
            "detect": ["24 a las 3"],
            "merge": [(5, 8)],
            "strict": [],
        },
        "Mittwoch, 17. April 2024 17:02": {
            "multi": ["17. April 2024"],
            "single": ["Mittwoch", "17:02"],
            "total": ["Mittwoch", "17. April 2024", "17:02"],
            "detect": ["Mittwoch, 17. April 2024 17:02"],
            "merge": [(4, 6), (9, 10)],
            "strict": ["17. April 2024 17:02"],
        },
        "am Mittwoch, 17. April 2024 um 16:58:57": {
            "multi": ["17. April 2024"],
            "single": ["Mittwoch", "16:58:57"],
            "total": ["Mittwoch", "17. April 2024", "16:58:57"],
            "detect": ["Mittwoch, 17. April 2024 um 16:58:57"],
            "merge": [(5, 7), (10, 12)],
            "strict": ["17. April 2024 um 16:58:57"],
        },
        "17.04.2024 17:33:23": {
            "multi": [],
            "single": ["17.04.2024", "17:33:23"],
            "total": ["17.04.2024", "17:33:23"],
            "detect": ["17.04.2024 17:33:23"],
            "merge": [(4, 5)],
            "strict": ["17.04.2024 17:33:23"],
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
def test_unite_unite_overlapping_words_no_overlap(get_time_detector_w_spacy):
    sent = "19/03/2025 something in between 10:30"
    doc = get_time_detector_w_spacy.nlp_spacy(sent)
    time_words = [(doc[0:1], None), (doc[4:5], None)]
    locations = [(0, 1), (4, 5)]
    updated_words, updated_locations = (
        get_time_detector_w_spacy.unite_overlapping_words(time_words, locations, None)
    )
    assert updated_words == time_words
    assert updated_locations == locations


@pytest.mark.pattern
def test_unite_unite_overlapping_words_overlap_end(get_time_detector_w_spacy):
    sent = "19/03/2025 10:30"
    doc = get_time_detector_w_spacy.nlp_spacy(sent)
    time_words = [(doc[0:1], None), (doc[1:2], None)]
    locations = [(0, 1), (1, 2)]
    updated_words, updated_locations = (
        get_time_detector_w_spacy.unite_overlapping_words(time_words, locations, doc)
    )
    assert len(updated_words) == 1
    assert updated_words[0][0].text == "19/03/2025 10:30"
    assert updated_locations == [(0, 2)]


@pytest.mark.pattern
def test_unite_overlapping_words_overlap_non_end(get_time_detector_w_spacy):
    sent = "17:13 something 19/03/2025 10:30 something in between 12:30"
    doc = get_time_detector_w_spacy.nlp_spacy(sent)
    time_words = [
        (doc[0:1], None),
        (doc[2:3], None),
        (doc[3:4], None),
        (doc[7:8], None),
    ]
    locations = [(0, 1), (2, 3), (3, 4), (7, 8)]
    updated_words, updated_locations = (
        get_time_detector_w_spacy.unite_overlapping_words(time_words, locations, doc)
    )
    assert len(updated_words) == 3
    assert updated_words[0][0].text == "17:13"
    assert updated_words[1][0].text == "19/03/2025 10:30"
    assert updated_words[2][0].text == "12:30"
    assert updated_locations == [(0, 1), (2, 4), (7, 8)]


@pytest.mark.pattern
def test_extract_date_time_multi_word_fr(get_time_detector_w_spacy, get_date_samples):
    sample_sentence, date_info = get_date_samples
    doc = get_time_detector_w_spacy.nlp_spacy(sample_sentence)
    multi_word_date_time, marked_locations = (
        get_time_detector_w_spacy.extract_date_time_multi_words(doc, "fr")
    )
    assert len(multi_word_date_time) == len(date_info["multi"])
    assert len(marked_locations) == len(date_info["multi"])
    for multi_time, sample_time in zip(multi_word_date_time, date_info["multi"]):
        assert multi_time[0].text == sample_time


@pytest.mark.pattern
def test_extract_date_time_single_word_fr(get_time_detector_w_spacy, get_date_samples):
    sample_sentence, date_info = get_date_samples
    doc = get_time_detector_w_spacy.nlp_spacy(sample_sentence)
    _, marked_locations = get_time_detector_w_spacy.extract_date_time_multi_words(
        doc, "fr"
    )
    word_date_time = get_time_detector_w_spacy.extract_date_time_single_word(
        doc, marked_locations
    )
    assert len(word_date_time) == len(date_info["single"])
    for single_time, sample_time in zip(word_date_time, date_info["single"]):
        assert single_time[0].text == sample_time


@pytest.mark.pattern
def test_get_start_end(get_time_detector_w_spacy, get_date_samples):
    sample_sentence, _ = get_date_samples
    doc = get_time_detector_w_spacy.nlp_spacy(sample_sentence)
    assert get_time_detector_w_spacy._get_start_end(doc[0]) == (0, 0)
    assert get_time_detector_w_spacy._get_start_end(doc[1]) == (1, 1)
    assert get_time_detector_w_spacy._get_start_end(doc[2:7]) == (2, 6)


@pytest.mark.pattern
def test_extract_date_time_fr(get_time_detector_w_spacy, get_date_samples):
    sample_sentence, date_info = get_date_samples
    doc = get_time_detector_w_spacy.nlp_spacy(sample_sentence)
    extracted_date_time = get_time_detector_w_spacy.extract_date_time(doc, "fr")
    assert len(extracted_date_time) == len(date_info["total"])
    for e_time, sample_time in zip(extracted_date_time, date_info["total"]):
        assert e_time[0].text == sample_time


@pytest.mark.pattern
def test_get_next_sibling(get_time_detector_w_spacy, get_date_samples):
    sample_sentence, _ = get_date_samples
    doc = get_time_detector_w_spacy.nlp_spacy(sample_sentence)
    token = doc[0]
    assert get_time_detector_w_spacy._get_next_sibling(token) == doc[1]
    assert get_time_detector_w_spacy._get_next_sibling(doc[len(doc) - 1]) is None


@pytest.mark.pattern
def test_is_time_mergeable(get_time_detector_w_spacy, get_date_samples):
    sample_sentence, date_info = get_date_samples
    doc = get_time_detector_w_spacy.nlp_spacy(sample_sentence)
    for s_id, e_id in date_info["merge"]:
        assert (
            get_time_detector_w_spacy.is_time_mergeable(doc[s_id], doc[e_id], doc)
            is True
        )
    assert get_time_detector_w_spacy.is_time_mergeable(doc[0], doc[7], doc) is False


@pytest.mark.pattern
def test_add_merged_datetime_empty(get_time_detector_w_spacy):
    merged_datetime = []
    new_text = "14/03/2025 à 10:30"
    new_item = (new_text, None, 0, len(new_text))
    get_time_detector_w_spacy.add_merged_datetime(merged_datetime, new_item)
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
def test_merge_date_time_fr(get_time_detector_w_spacy, get_date_samples):
    sample_sentence, date_info = get_date_samples
    doc = get_time_detector_w_spacy.nlp_spacy(sample_sentence)
    extracted_date_time = get_time_detector_w_spacy.extract_date_time(doc, "fr")
    merged_date_time = get_time_detector_w_spacy.merge_date_time(
        extracted_date_time, doc
    )
    assert len(merged_date_time) == len(date_info["detect"])
    for m_time, sample_time in zip(merged_date_time, date_info["detect"]):
        assert m_time[0] == sample_time


@pytest.mark.pattern
def test_merg_date_time_empty(get_time_detector_w_spacy):
    doc = get_time_detector_w_spacy.nlp_spacy("Alice")
    extracted_date_time = get_time_detector_w_spacy.extract_date_time(doc, "fr")
    merged_date_time = get_time_detector_w_spacy.merge_date_time(
        extracted_date_time, doc
    )
    assert len(merged_date_time) == 0


@pytest.mark.pattern
def test_merge_date_time_one_item(get_time_detector_w_spacy):
    doc = get_time_detector_w_spacy.nlp_spacy("14 mars 2025")
    extracted_date_time = get_time_detector_w_spacy.extract_date_time(doc, "fr")
    merged_date_time = get_time_detector_w_spacy.merge_date_time(
        extracted_date_time, doc
    )
    assert len(merged_date_time) == 1
    assert merged_date_time[0][0] == "14 mars 2025"
    assert merged_date_time[0][2] == 0
    assert merged_date_time[0][3] == 12


@pytest.mark.pattern
def test_merge_date_time_non_mergeable(get_time_detector_w_spacy):
    doc = get_time_detector_w_spacy.nlp_spacy(
        "24.03.2025 then something in between 10:30 then another thing in between 12:30"
    )
    extracted_date_time = get_time_detector_w_spacy.extract_date_time(doc, "fr")
    merged_date_time = get_time_detector_w_spacy.merge_date_time(
        extracted_date_time, doc
    )
    assert len(merged_date_time) == 3
    assert merged_date_time[0][0] == "24.03.2025"
    assert merged_date_time[1][0] == "10:30"
    assert merged_date_time[2][0] == "12:30"


@pytest.mark.pattern
def test_filter_non_numbers(get_time_detector):
    date_times = [
        ("14 mars 2025", None, 0, 12),
        ("10:30", None, 13, 18),
        ("17:23", None, 19, 24),
        ("a", None, 25, 26),
        ("b", None, 27, 28),
        ("An", None, 29, 31),
    ]
    assert get_time_detector.filter_non_numbers([]) == []
    assert get_time_detector.filter_non_numbers(date_times) == date_times[0:3]


@pytest.mark.pattern
def test_get_date_time_fr(get_time_detector, get_date_samples):
    sample_sentence, date_info = get_date_samples
    results = get_time_detector.get_date_time(sample_sentence, "fr")
    assert len(results) == len(date_info["detect"])
    for result, sample_time in zip(results, date_info["detect"]):
        assert result[0] == sample_time


@pytest.mark.pattern
def test_get_date_time_fr_non_numbers(get_time_detector):
    # somehow "An" and "a" are detected as dates
    assert get_time_detector.get_date_time("An", "fr") == []
    assert get_time_detector.get_date_time("a", "fr") == []


@pytest.mark.strict
def test_get_date_time_fr_strict(get_time_detector_strict, get_date_samples):
    sample_sentence, date_info = get_date_samples
    results = get_time_detector_strict.get_date_time(sample_sentence, "fr")
    assert len(results) == len(date_info["strict"])
    for result, sample_time in zip(results, date_info["strict"]):
        assert result[0] == sample_time


def test_get_date_time_fr_strict_single_data(get_time_detector_strict):
    sample_sentence = "Enviado el: martes, 07 de mayo de 2013 12:52"
    results = get_time_detector_strict.get_date_time(sample_sentence, "es")
    assert len(results) == 0

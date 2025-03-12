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

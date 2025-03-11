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
    },
    "relative": {
        "tomorrow": datetime.date.today() + datetime.timedelta(days=1),
        "today": datetime.date.today(),
        "two weeks ago": datetime.date.today() - datetime.timedelta(days=14),
        "in two weeks": datetime.date.today() + datetime.timedelta(days=14),
        "2 weeks ago": datetime.date.today() - datetime.timedelta(days=14),
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


def test_find_dates(get_time_detector):
    extra_info = "The date in the email is: "
    for date_str, date_obj in sample_dates["absolute"].items():
        assert get_time_detector.find_dates(extra_info + date_str) == [date_obj]
    # for date_str, date_obj in sample_dates["relative"].items():
    #     assert get_time_detector.find_dates(extra_info + date_str) == [date_obj]
    for date_str in sample_dates["invalid"]:
        assert get_time_detector.find_dates(extra_info + date_str) == []
    # for date_str, date_obj in sample_dates["confusing"].items():
    #     assert get_time_detector.find_dates(extra_info + date_str) == [date_obj]

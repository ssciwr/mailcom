from mailcom import inout
import pytest
from pathlib import Path
from importlib import resources
import datetime
import filecmp
import csv

pkg = resources.files("mailcom")

FILE_PATH = Path(pkg / "test" / "data" / "Bonjour Agathe.eml")
XML_PATH = Path(pkg / "test" / "data" / "test.out")

TEXT_REF = "J'espère que tu vas bien!"
XML_REF = '<?xml version="1.0" encoding="UTF-8" ?><email><content type="str">'


@pytest.fixture()
def get_instant(tmp_path):
    return inout.InoutHandler(tmp_path)


def test_list_of_files(get_instant):
    with pytest.raises(ValueError):
        get_instant.list_of_files()
    p = get_instant.directory_name / "test.eml"
    p.write_text("test")
    get_instant.list_of_files()
    assert len(get_instant.email_path_list) != 0
    get_instant2 = inout.InoutHandler("nonexistingDir")
    with pytest.raises(OSError):
        get_instant2.list_of_files()
    p = get_instant.directory_name / "test2.html"
    p.write_text("test2")
    p = get_instant.directory_name / "test3.xml"
    p.write_text("test3")
    get_instant.list_of_files()
    assert get_instant.directory_name / "test3.xml" not in get_instant.email_path_list


def test_get_html_text(get_instant):
    html = """<html><head><title>Test</title></head></html>"""
    assert get_instant.get_html_text(html) == "Test"
    noHtml = """Test"""
    assert get_instant.get_html_text(noHtml) == "Test"


def test_data_to_xml(get_instant, tmp_path):
    xml_content = {
        "content": "This is nothing more than a test",
        "date": "2024-04-17T15:13:56+00:00",
        "attachment": 2,
        "attachement type": {"jpg", "jpg"},
    }
    xml = get_instant.data_to_xml(xml_content)
    get_instant.write_file(xml, tmp_path / "test")
    assert filecmp.cmp(XML_PATH, tmp_path / "test.out")


def test_extract_email_info(get_instant):
    # Test with a valid email file
    email_info = get_instant.extract_email_info(FILE_PATH)
    assert email_info["content"].startswith(TEXT_REF)
    assert email_info["date"] == datetime.datetime(
        2024, 4, 17, 15, 13, 56, tzinfo=datetime.timezone.utc
    )
    assert email_info["attachment"] == 2
    assert email_info["attachement type"] == ["jpg", "jpg"]

    # Test with a non-existing file
    with pytest.raises(OSError):
        get_instant.extract_email_info(get_instant.directory_name / "nonexisting.eml")


def test_process_emails(get_instant):
    # Create some test email files
    email_file_1 = get_instant.directory_name / "test1.eml"
    email_file_1.write_text("Content of test email 1")
    email_file_2 = get_instant.directory_name / "test2.eml"
    email_file_2.write_text("Content of test email 2")

    # Update the directory name and list of files
    get_instant.list_of_files()

    # Process the emails
    get_instant.process_emails()

    # Check if the emails were processed and added to the email list
    assert len(get_instant.email_list) == 2
    assert "Content of test email" in get_instant.email_list[0]["content"]
    assert "Content of test email" in get_instant.email_list[1]["content"]


def test_write_csv(get_instant, tmp_path):
    # Create some test email data
    email_data = [
        {
            "content": "Content of test email 1",
            "date": "2024-04-17T15:13:56+00:00",
            "attachment": 1,
            "attachement type": ["jpg"],
        },
        {
            "content": "Content of test email 2",
            "date": "2024-04-18T15:13:56+00:00",
            "attachment": 0,
            "attachement type": [],
        },
    ]
    get_instant.email_list = email_data

    # Define the output CSV file path
    csv_file = tmp_path / "test_emails.csv"

    # Write the email data to CSV
    get_instant.write_csv(csv_file)

    # Read the CSV file and verify its contents
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["content"] == "Content of test email 1"
        assert rows[0]["date"] == "2024-04-17T15:13:56+00:00"
        assert rows[0]["attachment"] == "1"
        assert rows[0]["attachement type"] == "['jpg']"
        assert rows[1]["content"] == "Content of test email 2"
        assert rows[1]["date"] == "2024-04-18T15:13:56+00:00"
        assert rows[1]["attachment"] == "0"
        assert rows[1]["attachement type"] == "[]"


def test_get_email_list(get_instant):
    # Create some test email data
    email_data = [
        {
            "content": "Content of test email 1",
            "date": "2024-04-17T15:13:56+00:00",
            "attachment": 1,
            "attachement type": ["jpg"],
        },
        {
            "content": "Content of test email 2",
            "date": "2024-04-18T15:13:56+00:00",
            "attachment": 0,
            "attachement type": [],
        },
    ]
    get_instant.email_list = email_data

    # Get the email list iterator
    email_list_iter = get_instant.get_email_list()

    # Verify the contents of the email list
    assert next(email_list_iter) == email_data[0]
    assert next(email_list_iter) == email_data[1]

    # Verify that the iterator is exhausted
    with pytest.raises(StopIteration):
        next(email_list_iter)

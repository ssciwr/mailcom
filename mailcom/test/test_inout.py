from mailcom import inout
import pytest
from pathlib import Path
from importlib import resources
import datetime
import filecmp

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
    assert len(get_instant.email_list) != 0
    get_instant2 = inout.InoutHandler("nonexistingDir")
    with pytest.raises(OSError):
        get_instant2.list_of_files()
    p = get_instant.directory_name / "test2.html"
    p.write_text("test2")
    p = get_instant.directory_name / "test3.xml"
    p.write_text("test3")
    get_instant.list_of_files()
    assert get_instant.directory_name / "test3.xml" not in get_instant.email_list


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
    assert "Content of test email 1" in get_instant.email_list[0]["content"]
    assert "Content of test email 2" in get_instant.email_list[1]["content"]

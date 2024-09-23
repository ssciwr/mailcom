from mailcom import inout
import pytest
from pathlib import Path
from importlib import resources
import datetime

pkg = resources.files("mailcom")

FILE_PATH = Path(pkg / "test" / "data" / "Bonjour Agathe.eml")

TEXT_REF = "J'espère que tu vas bien!"

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

def test_get_text(get_instant):
    p = get_instant.directory_name / "test.eml"
    p.write_text("test")
    extracted_text = get_instant.get_text(p)
    assert extracted_text == 'test'
    text = get_instant.get_text(FILE_PATH)
    assert text[0:25] == TEXT_REF
    assert get_instant.email_content["date"] == datetime.datetime(2024, 4, 17, 15, 13, 56, tzinfo=datetime.timezone.utc)
    assert get_instant.email_content["attachment"] == 2
    assert get_instant.email_content["attachement type"] == ['jpg', 'jpg']
    with pytest.raises(OSError):
        get_instant.get_text(get_instant.directory_name / "nonexisting.eml")

def test_get_html_text(get_instant):
    html = """<html><head><title>Test</title></head></html>"""
    assert get_instant.get_html_text(html) == 'Test'
    noHtml = """Test"""
    assert get_instant.get_html_text(noHtml) == 'Test'
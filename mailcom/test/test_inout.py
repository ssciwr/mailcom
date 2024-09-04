from mailcom.inout import list_of_files, get_text, get_html_text
import pytest
from pathlib import Path

def test_list_of_files_found(tmp_path):
    p = tmp_path / "test.eml"
    p.write_text("test")
    assert len(list_of_files(tmp_path)) != 0

def test_list_of_files_empty(tmp_path):
    with pytest.raises(ValueError):
        list_of_files(tmp_path)

def test_list_of_files_dir_not_existing():
    with pytest.raises(OSError):
        list_of_files("nonexistingDir")

def test_list_of_files_correct_format(tmp_path):
    p = tmp_path / "test.eml"
    p.write_text("test")
    p = tmp_path / "test2.html"
    p.write_text("test2")
    p = tmp_path / "test3.xml"
    p.write_text("test3")
    assert tmp_path / "test3.xml" not in list_of_files(tmp_path)

def test_get_text(tmp_path):
    p = tmp_path / "test.eml"
    p.write_text("test")
    assert get_text(p) == 'test'

def test_get_text_err():
    with pytest.raises(OSError):
        list_of_files("nonexistingDir")

def test_get_html_text():
    html = """<html><head><title>Test</title></head></html>"""
    assert get_html_text(html) == 'Test'

def test_get_html_text_noHtml():
    noHtml = """Test"""
    assert get_html_text(noHtml) == 'Test'

def test_get_text_no_file(tmp_path):
    p = tmp_path / "test.eml"
    with pytest.raises(OSError):
        get_text(p)
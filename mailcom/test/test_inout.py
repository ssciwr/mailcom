from mailcom.inout import list_of_files

def test_list_of_files_found(tmp_path):
    p = tmp_path / "test.eml"
    p.write_text("test")
    assert len(list_of_files(tmp_path)) != 0, "The list is empty"

def test_list_of_files_empty(tmp_path):
    assert len(list_of_files(tmp_path)) == 0, "The list is not empty"
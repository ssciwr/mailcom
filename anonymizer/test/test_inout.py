import inout as io

def test_list_of_files(tmpdir):
    p = tmpdir.mkdir("sub").join("test.eml")
    list = io.list_of_files(tmpdir)
    assert list.assertTrue()
    assert 0
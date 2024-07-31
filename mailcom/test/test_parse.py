import parse as pe


# these worked when we were using strings
# with the update to Path, we need to change the tests
def test_check_dir(tmpdir):
    mydir = tmpdir.mkdir("sub")
    assert pe.check_dir(str(mydir))
    assert not pe.check_dir(str(tmpdir.join("sub2")))


def test_make_dir(tmpdir):
    mydir = tmpdir.join("sub")
    pe.make_dir(str(mydir))
    assert mydir.check()

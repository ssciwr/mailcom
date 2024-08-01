from mailcom.parse import make_dir, check_dir
import pytest


# these worked when we were using strings
# with the update to Path, we need to change the tests
def test_check_dir(tmpdir):
    mydir = tmpdir.mkdir("sub")
    assert check_dir(str(mydir))
    with pytest.raises(OSError):
        check_dir(str(tmpdir.join("sub2")))


def test_make_dir(tmpdir):
    mydir = tmpdir.join("sub")
    make_dir(str(mydir))
    assert mydir.check()

def test_check_dir_fail():
    with pytest.raises(OSError):
        check_dir(str("mydir"))

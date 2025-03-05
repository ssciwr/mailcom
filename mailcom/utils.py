import os


def check_dir(path: str) -> bool:
    if not os.path.exists(path):
        raise OSError("Path {} does not exist".format(path))
    else:
        return True


def make_dir(path: str):
    # make directory at path
    os.makedirs(path + "/")
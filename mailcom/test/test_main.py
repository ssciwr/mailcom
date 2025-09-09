import pytest
from mailcom import main
from mailcom import utils
from mailcom.inout import InoutHandler
import json
from pathlib import Path
from importlib import resources
import csv
import copy


def get_files(dir_path: Path, name_phrase: str) -> list[Path]:
    """
    Get all files in a directory that contain the name_phrase in their name.
    """
    return [
        file
        for file in dir_path.iterdir()
        if file.is_file() and name_phrase in file.name
    ]


def test_get_input_handler_csv_empty(tmp_path):
    inpath = tmp_path / "test.csv"
    # empty file
    open(inpath, "w", newline="", encoding="utf-8").close()

    inout_hl = main.get_input_handler(inpath, in_type="csv")
    assert inout_hl.email_list == []


def test_get_input_handler_csv_unmatch(tmp_path):
    inpath = tmp_path / "test.csv"
    with open(inpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["no", "content"])
        writer.writerow(
            [
                "1",
                "Content of test email 1",
            ]
        )

    inout_hl = main.get_input_handler(
        inpath, in_type="csv", col_names=["nonexisting"], unmatched_keyword="unmatched"
    )
    emails = inout_hl.get_email_list()
    email = next(emails)
    assert email["content"] == "unmatched"
    assert email["date"] is None
    assert email["attachment"] is None
    assert email["attachment type"] is None
    assert email["subject"] is None


def test_get_input_handler_dir(tmpdir):
    indir = tmpdir.join("sub")
    utils.make_dir(indir)
    with pytest.raises(ValueError):
        main.get_input_handler(indir, in_type="dir")


def test_is_valid_settings():
    settings = {"pseudo_fields": ["content", "subject"]}
    assert main.is_valid_settings(settings) is True
    settings = {"pseudo_fields": "content"}
    assert main.is_valid_settings(settings) is False
    settings = {"pseudo_fields": [1, 2]}
    assert main.is_valid_settings(settings) is False

    settings = {"csv_col_unmatched_keyword": True}
    assert main.is_valid_settings(settings) is False
    settings = {"csv_col_unmatched_keyword": "error"}
    assert main.is_valid_settings(settings) is True

    settings = {"default_lang": 1}
    assert main.is_valid_settings(settings) is False
    settings = {"default_lang": "fr"}
    assert main.is_valid_settings(settings) is True
    settings = {"default_lang": "unknown"}
    assert main.is_valid_settings(settings) is True
    settings = {"default_lang": ""}
    assert main.is_valid_settings(settings) is True

    settings = {"datetime_detection": True}
    assert main.is_valid_settings(settings) is True
    settings = {"datetime_detection": "test"}
    assert main.is_valid_settings(settings) is False

    settings = {"time_parsing": "strict"}
    assert main.is_valid_settings(settings) is True
    settings = {"time_parsing": "unknown"}
    assert main.is_valid_settings(settings) is False

    settings = {"pseudo_emailaddresses": True}
    assert main.is_valid_settings(settings) is True
    settings = {"pseudo_emailaddresses": "test"}
    assert main.is_valid_settings(settings) is False

    settings = {"pseudo_ne": False}
    assert main.is_valid_settings(settings) is True
    settings = {"pseudo_ne": "test"}
    assert main.is_valid_settings(settings) is False

    settings = {"pseudo_numbers": True}
    assert main.is_valid_settings(settings) is True
    settings = {"pseudo_numbers": "test"}
    assert main.is_valid_settings(settings) is False

    settings = {"pseudo_first_names": "test"}
    assert main.is_valid_settings(settings) is False
    settings = {"pseudo_first_names": []}
    assert main.is_valid_settings(settings) is False
    settings = {"pseudo_first_names": {}}
    assert main.is_valid_settings(settings) is False
    settings = {"pseudo_first_names": {"test": "test"}}
    assert main.is_valid_settings(settings) is True
    settings = {"pseudo_first_names": {"test": "test", "test2": "test2"}}
    assert main.is_valid_settings(settings) is True

    settings = {"lang_detection_lib": "langid"}
    assert main.is_valid_settings(settings) is True
    settings = {"lang_detection_lib": "unknown"}
    assert main.is_valid_settings(settings) is False

    settings = {"lang_pipeline": None}
    assert main.is_valid_settings(settings) is True
    settings = {"lang_pipeline": "unknown"}
    assert main.is_valid_settings(settings) is False
    settings = {"lang_pipeline": {}}
    assert main.is_valid_settings(settings) is False
    settings = {"lang_pipeline": {"test": "test"}}
    assert main.is_valid_settings(settings) is False
    settings = {"lang_pipeline": {"task": "test"}}
    assert main.is_valid_settings(settings) is False
    settings = {"lang_pipeline": {"model": "test"}}
    assert main.is_valid_settings(settings) is False
    settings = {"lang_pipeline": {"task": "test", "model": "test"}}
    assert main.is_valid_settings(settings) is True

    settings = {"spacy_model": "test"}
    assert main.is_valid_settings(settings) is True
    settings = {"spacy_model": {}}
    assert main.is_valid_settings(settings) is False

    settings = {"ner_pipeline": None}
    assert main.is_valid_settings(settings) is True
    settings = {"ner_pipeline": "unknown"}
    assert main.is_valid_settings(settings) is False

    settings = {"unknown_key": "value"}
    assert main.is_valid_settings(settings) is False


def test_update_new_settings_empty():
    updated = main._update_new_settings({"test": "test"}, {})
    assert updated is False

    with pytest.raises(ValueError):
        main._update_new_settings({}, {"test": "test"})


def test_update_new_settings_not_updated():
    # invalid key
    with pytest.warns(UserWarning):
        updated = main._update_new_settings({"default_lang": "fr"}, {"test": "test"})
    assert updated is False

    # invalid structure
    with pytest.warns(UserWarning):
        updated = main._update_new_settings(
            {"default_lang": "fr"}, {"default_lang": True}
        )
    assert updated is False

    # same value
    updated = main._update_new_settings({"default_lang": "fr"}, {"default_lang": "fr"})
    assert updated is False


def test_update_new_settings_updated():
    settings = {"default_lang": "fr"}
    updated = main._update_new_settings(settings, {"default_lang": "es"})
    assert updated is True
    assert settings.get("default_lang") == "es"


def test_save_settings_to_file(tmpdir):
    settings = {"default_lang": "de"}

    # none dir path
    main.save_settings_to_file(settings)
    saved_files = get_files(Path.cwd(), "updated_workflow_settings_")
    assert len(saved_files) == 1
    with open(saved_files[0], "r", encoding="utf-8") as f:
        updated_settings = json.load(f)
    assert updated_settings.get("default_lang") == "de"
    saved_files[0].unlink()  # remove the file

    # valid dir path
    directory = Path(tmpdir.mkdir("test"))
    main.save_settings_to_file(settings, directory)
    saved_files = get_files(directory, "updated_workflow_settings_")
    assert len(saved_files) == 1
    with open(saved_files[0], "r", encoding="utf-8") as f:
        updated_settings = json.load(f)
    assert updated_settings.get("default_lang") == "de"

    # invalid dir path
    file_path = Path(__file__).absolute()
    with pytest.raises(ValueError):
        main.save_settings_to_file(settings, file_path)


def test_get_workflow_settings_default():
    settings = main.get_workflow_settings()
    assert settings.get("default_lang") == "fr"

    settings = main.get_workflow_settings("default")
    assert settings.get("default_lang") == "fr"


def test_get_workflow_settings_file(tmp_path):
    setting_path = tmp_path / "settings.json"

    # invalid cases
    # not existing file
    with pytest.warns(UserWarning):
        settings = main.get_workflow_settings(setting_path)
    assert settings.get("default_lang") == "fr"

    # empty file
    open(setting_path, "w", newline="", encoding="utf-8").close()
    with pytest.warns(UserWarning):
        settings = main.get_workflow_settings(setting_path)
    assert settings.get("default_lang") == "fr"

    # invalid json file
    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        f.write("test")
    with pytest.warns(UserWarning):
        settings = main.get_workflow_settings(setting_path)
    assert settings.get("default_lang") == "fr"

    # invalid json file against the schema
    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        json.dump({"test": "test"}, f)
    with pytest.warns(UserWarning):
        settings = main.get_workflow_settings(setting_path)
    assert settings.get("default_lang") == "fr"

    # valid json file
    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        json.dump({"default_lang": "es"}, f)
    settings = main.get_workflow_settings(setting_path)
    assert settings.get("default_lang") == "es"


def test_get_workflow_settings_new_settings(tmp_path, tmpdir):
    new_settings = {"default_lang": "es"}

    # update default settings
    settings = main.get_workflow_settings(
        new_settings=new_settings, save_updated_settings=False
    )
    assert settings.get("default_lang") == "es"

    # update settings from file
    setting_path = tmp_path / "settings.json"
    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        json.dump({"default_lang": "fr"}, f)
    settings = main.get_workflow_settings(setting_path)
    assert settings.get("default_lang") == "fr"
    settings = main.get_workflow_settings(
        setting_path, new_settings=new_settings, save_updated_settings=False
    )
    assert settings.get("default_lang") == "es"

    # update settings from file with invalid new settings
    new_settings = {"test": "test"}
    with pytest.warns(UserWarning):
        settings = main.get_workflow_settings(setting_path, new_settings=new_settings)
    assert settings.get("default_lang") == "fr"

    # update settings from file, save updated settings
    new_settings = {"default_lang": "es"}
    directory = Path(tmpdir.mkdir("test"))
    settings = main.get_workflow_settings(
        setting_path,
        new_settings=new_settings,
        updated_setting_dir=directory,
        save_updated_settings=True,
    )
    assert settings.get("default_lang") == "es"
    created_files = get_files(directory, "updated_workflow_settings_")
    assert len(created_files) == 1
    with open(created_files[0], "r", encoding="utf-8") as f:
        updated_settings = json.load(f)
    assert updated_settings.get("default_lang") == "es"


@pytest.fixture()
def get_data():
    return [
        {
            "content": "Alice (alice@gmail.com) viendra au bâtiment à 10h00. "
            "Nous nous rendrons ensuite au MeetingPoint"
        },
        {
            "content": "Esta foto fue tomada por Alice el 28.03.2025 a las 10:30. "
            "Compruébelo en el archivo adjunto",
            "attachment": 1,
            "attachment type": ["jpg"],
        },
    ]


def _modify_data(base_data: list, updates: tuple, remove_indices=None):
    data = copy.deepcopy(base_data)

    for index, field, value in updates:
        data[index][field] = value

    if remove_indices:
        for index in sorted(remove_indices, reverse=True):
            data.pop(index)

    return data


@pytest.fixture()
def get_data_w_subject(get_data):
    return _modify_data(
        get_data,
        updates=[
            (0, "subject", "Rendez-vous à 10h00"),
            (1, "subject", "Foto del 28.03.2025"),
        ],
    )


@pytest.fixture()
def get_data_small(get_data):
    return _modify_data(
        get_data,
        updates=[
            (
                1,
                "content",
                "Esta foto fue tomada por Alice e Angel el 28.03.2025 a las 10:30. "
                "Compruébelo en el archivo adjunto",
            )
        ],
        remove_indices=[0],
    )


@pytest.fixture()
def get_data_small_w_subject(get_data_small):
    return _modify_data(
        get_data_small,
        updates=[(0, "subject", "Foto del 28.03.2025 por Angel e Alice")],
    )


@pytest.fixture()
def get_settings():
    pkg = resources.files("mailcom")
    setting_path = Path(pkg / "test" / "settings_for_testing.json")
    return json.load(open(setting_path, "r", encoding="utf-8"))


@pytest.fixture()
def get_inout_hl():
    return InoutHandler()


def test_process_data_default(get_data, get_settings, get_inout_hl):
    get_inout_hl.email_list = get_data
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    emails = get_inout_hl.get_email_list()
    email_1 = next(emails)
    email_2 = next(emails)

    assert email_1.get("cleaned_content") == email_1.get("content")
    assert email_1.get("lang").get("content") == "fr"
    assert email_1.get("detected_datetime").get("content") == []
    assert (
        email_1.get("pseudo_content")
        == "Claude [email] viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au [location]"
    )
    assert email_1.get("sentences").get("content") == [
        "Alice (alice@gmail.com) viendra au bâtiment à 10h00.",
        "Nous nous rendrons ensuite au MeetingPoint",
    ]
    assert email_1.get("sentences_after_email").get("content") == [
        "Alice [email] viendra au bâtiment à 10h00.",
        "Nous nous rendrons ensuite au MeetingPoint",
    ]

    assert email_2.get("cleaned_content") == email_2.get("content")
    assert email_2.get("lang").get("content") == "es"
    assert email_2.get("detected_datetime").get("content") == ["28.03.2025 a las 10:30"]
    assert (
        email_2.get("pseudo_content")
        == "Esta foto fue tomada por José el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )
    assert email_2.get("sentences").get("content") == [
        "Esta foto fue tomada por Alice el 28.03.2025 a las 10:30.",
        "Compruébelo en el archivo adjunto",
    ]
    assert email_2.get("sentences_after_email").get("content") == [
        "Esta foto fue tomada por Alice el 28.03.2025 a las 10:30.",
        "Compruébelo en el archivo adjunto",
    ]


def test_process_data_no_lang(get_data, get_settings, get_inout_hl):
    get_settings["default_lang"] = "de"
    get_inout_hl.email_list = get_data
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    emails = get_inout_hl.get_email_list()
    email_1 = next(emails)
    email_2 = next(emails)

    assert email_1.get("lang").get("content") == "de"
    assert (
        email_1.get("pseudo_content")
        == "Mika [email] viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au [location]"
    )

    assert email_2.get("lang").get("content") == "de"
    assert (
        email_2.get("pseudo_content")
        == "Esta foto fue tomada por Mika el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )


def test_process_data_no_datetime(get_data, get_settings, get_inout_hl):
    get_settings["datetime_detection"] = False
    get_inout_hl.email_list = get_data
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    emails = get_inout_hl.get_email_list()
    next(emails)
    email_2 = next(emails)

    assert email_2.get("detected_datetime").get("content") is None
    assert (
        email_2.get("pseudo_content") == "Esta foto fue tomada por José el "
        "[number].[number].[number] a las [number]:[number]. "
        "Compruébelo en el archivo adjunto"
    )


def test_process_data_no_email(get_data, get_settings, get_inout_hl):
    get_settings["pseudo_emailaddresses"] = False
    get_inout_hl.email_list = get_data
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    email_1 = next(get_inout_hl.get_email_list())

    assert (
        email_1.get("pseudo_content")
        == "Claude (alice@gmail.com) viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au [location]"
    )
    assert email_1.get("sentences_after_email") == {}


def test_process_data_no_ne(get_data, get_settings, get_inout_hl):
    get_settings["pseudo_ne"] = False
    get_inout_hl.email_list = get_data
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    emails = get_inout_hl.get_email_list()
    email_1 = next(emails)
    email_2 = next(emails)

    assert (
        email_1.get("pseudo_content")
        == "Alice [email] viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au MeetingPoint"
    )

    assert (
        email_2.get("pseudo_content")
        == "Esta foto fue tomada por Alice el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )


def test_process_data_matching_pseudonym(get_data, get_settings, get_inout_hl):
    get_inout_hl.email_list = get_data
    new_settings = {
        "pseudo_first_names": {
            "es": ["Alice", "Angel", "Alex"],
            "fr": ["Claude", "Dominique", "Alice"],
        }
    }
    main._update_new_settings(get_settings, new_settings=new_settings)
    # check that pseudonyms have been updated
    assert get_settings["pseudo_first_names"] == new_settings["pseudo_first_names"]
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    emails = get_inout_hl.get_email_list()
    email_1 = next(emails)
    email_2 = next(emails)

    assert email_1.get("cleaned_content") == email_1.get("content")
    assert email_1.get("lang").get("content") == "fr"
    assert email_1.get("detected_datetime").get("content") == []
    assert (
        email_1.get("pseudo_content")
        == "Claude [email] viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au [location]"
    )
    assert email_1.get("sentences").get("content") == [
        "Alice (alice@gmail.com) viendra au bâtiment à 10h00.",
        "Nous nous rendrons ensuite au MeetingPoint",
    ]
    assert email_1.get("sentences_after_email").get("content") == [
        "Alice [email] viendra au bâtiment à 10h00.",
        "Nous nous rendrons ensuite au MeetingPoint",
    ]

    assert email_2.get("cleaned_content") == email_2.get("content")
    assert email_2.get("lang").get("content") == "es"
    assert email_2.get("detected_datetime").get("content") == ["28.03.2025 a las 10:30"]
    assert (
        email_2.get("pseudo_content")
        == "Esta foto fue tomada por Angel el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )
    assert email_2.get("sentences").get("content") == [
        "Esta foto fue tomada por Alice el 28.03.2025 a las 10:30.",
        "Compruébelo en el archivo adjunto",
    ]
    assert email_2.get("sentences_after_email").get("content") == [
        "Esta foto fue tomada por Alice el 28.03.2025 a las 10:30.",
        "Compruébelo en el archivo adjunto",
    ]


def test_process_data_multiple_same_pseudonyms(
    get_data_small, get_settings, get_inout_hl
):
    get_inout_hl.email_list = get_data_small
    new_settings = {
        "pseudo_first_names": {
            "es": [
                "Alice",
                "Alaya",
                "Angel",
            ],
        }
    }
    main._update_new_settings(get_settings, new_settings=new_settings)
    # check that pseudonyms have been updated
    assert get_settings["pseudo_first_names"] == new_settings["pseudo_first_names"]
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    emails = get_inout_hl.get_email_list()
    email_2 = next(emails)

    assert email_2.get("cleaned_content") == email_2.get("content")
    assert email_2.get("lang").get("content") == "es"
    assert email_2.get("detected_datetime").get("content") == ["28.03.2025 a las 10:30"]
    assert (
        email_2.get("pseudo_content")
        == "Esta foto fue tomada por Alaya e Alaya el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )
    assert email_2.get("sentences").get("content") == [
        "Esta foto fue tomada por Alice e Angel el 28.03.2025 a las 10:30.",
        "Compruébelo en el archivo adjunto",
    ]
    assert email_2.get("sentences_after_email").get("content") == [
        "Esta foto fue tomada por Alice e Angel el 28.03.2025 a las 10:30.",
        "Compruébelo en el archivo adjunto",
    ]


def test_process_data_same_pseudonym_not_enough_pseudos(
    get_data_small, get_settings, get_inout_hl
):
    get_inout_hl.email_list = get_data_small
    new_settings = {
        "pseudo_first_names": {
            "es": [
                "Alice",
            ],
        }
    }
    main._update_new_settings(get_settings, new_settings=new_settings)
    # check that pseudonyms have been updated
    assert get_settings["pseudo_first_names"] == new_settings["pseudo_first_names"]
    with pytest.raises(ValueError):
        main.process_data(get_inout_hl.get_email_list(), get_settings)


def test_process_data_no_numbers(get_data, get_settings, get_inout_hl):
    get_settings["pseudo_numbers"] = False
    get_inout_hl.email_list = get_data
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    emails = get_inout_hl.get_email_list()
    email_1 = next(emails)
    email_2 = next(emails)

    assert (
        email_1.get("pseudo_content") == "Claude [email] viendra au bâtiment à 10h00. "
        "Nous nous rendrons ensuite au [location]"
    )

    assert (
        email_2.get("pseudo_content")
        == "Esta foto fue tomada por José el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )


def test_process_data_empty_email(get_data, get_settings, get_inout_hl):
    # no content key
    get_inout_hl.email_list = get_data
    get_inout_hl.email_list.append({"no-content": "test"})
    main.process_data(get_inout_hl.get_email_list(), get_settings)
    emails = get_inout_hl.get_email_list()
    next(emails)
    next(emails)
    email_3 = next(emails)
    assert "pseudo_content" not in email_3

    # unmatched content
    get_inout_hl.email_list = get_data
    get_inout_hl.email_list.append({"content": "unmatched"})
    main.process_data(get_inout_hl.get_email_list(), get_settings)
    emails = get_inout_hl.get_email_list()
    next(emails)
    next(emails)
    email_3 = next(emails)
    assert "pseudo_content" not in email_3


def test_process_data_with_subject(get_data_w_subject, get_settings, get_inout_hl):
    get_inout_hl.email_list = get_data_w_subject
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    emails = get_inout_hl.get_email_list()
    email_1 = next(emails)
    email_2 = next(emails)

    assert email_1.get("cleaned_subject") == email_1.get("subject")
    assert email_1.get("pseudo_subject") == "Rendez-vous à [number]h[number]"

    assert email_2.get("cleaned_subject") == email_2.get("subject")
    assert email_2.get("pseudo_subject") == "Foto del [number].[number].[number]"


def test_process_data_with_subject_multiple_same_pseudonyms(
    get_data_small_w_subject, get_settings, get_inout_hl
):
    get_inout_hl.email_list = get_data_small_w_subject
    new_settings = {
        "pseudo_first_names": {
            "es": [
                "Alice",
                "Alaya",
                "Angel",
                "Alex",
            ],
            "it": [
                "Alice",
                "Alaya",
                "Angel",
                "Alex",
            ],  # somehow the subject is detected as Italian
        }
    }
    main._update_new_settings(get_settings, new_settings=new_settings)
    # check that pseudonyms have been updated
    assert get_settings["pseudo_first_names"] == new_settings["pseudo_first_names"]
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    emails = get_inout_hl.get_email_list()
    email = next(emails)

    assert email.get("cleaned_subject") == email.get("subject")
    assert (
        email.get("pseudo_subject")
        == "Foto del [number].[number].[number] por Alaya e Alex"
    )
    assert email.get("pseudo_content") == (
        "Esta foto fue tomada por Alex e Alaya el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )


def test_process_data_with_subject_with_prev_ne_list(
    get_data_small_w_subject, get_settings, get_inout_hl
):
    # simplify the test without duplicate names
    data = copy.deepcopy(get_data_small_w_subject)
    data[0]["content"] = (
        "Esta foto fue tomada por Alice e Tony el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )
    # switch per name position to check that the prev_ne_list works
    data[0]["subject"] = "Foto del 28.03.2025 por Tony e Alice"

    get_inout_hl.email_list = data

    # make sure only use es pseudonyms
    new_settings = copy.deepcopy(get_settings)
    new_settings["default_lang"] = "es"

    main.process_data(get_inout_hl.get_email_list(), new_settings)

    emails = get_inout_hl.get_email_list()
    email = next(emails)

    assert (
        email.get("pseudo_subject")
        == "Foto del [number].[number].[number] por José e Angel"
    )

    assert email.get("pseudo_content") == (
        "Esta foto fue tomada por Angel e José el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )


def test_write_output_data_csv(get_data, tmp_path, get_inout_hl):
    outpath = tmp_path / "test_output.csv"
    get_inout_hl.email_list = get_data
    main.write_output_data(get_inout_hl, outpath)

    with open(outpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 3  # header + 2 emails
        assert (
            lines[1] == "Alice (alice@gmail.com) viendra au bâtiment à 10h00. "
            "Nous nous rendrons ensuite au MeetingPoint,,\n"
        )
        assert (
            lines[2] == "Esta foto fue tomada por Alice el 28.03.2025 a las 10:30. "
            "Compruébelo en el archivo adjunto,1.0,['jpg']\n"
        )


def test_write_output_data_xml(get_data, tmp_path, get_inout_hl):
    outpath = tmp_path / "test_output.xml"
    get_inout_hl.email_list = get_data
    main.write_output_data(get_inout_hl, outpath)

    with open(outpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        assert lines[0].startswith('<?xml version="1.0" encoding="UTF-8" ?>')
        assert lines[0].endswith("</email_list>")
        assert lines[0].count('<email type="dict">') == 2


def test_write_output_data_invalid(get_data, tmp_path, get_inout_hl, tmpdir):
    # invalid file type
    outpath = tmp_path / "test_output.txt"
    with pytest.raises(ValueError):
        main.write_output_data(get_inout_hl, outpath)

    # empty data to write
    outpath = tmp_path / "test_output.csv"
    with pytest.raises(ValueError):
        main.write_output_data(get_inout_hl, outpath)

    # empty path
    get_inout_hl.email_list = get_data
    with pytest.raises(ValueError):
        main.write_output_data(get_inout_hl, "")

    # invalid file path
    get_inout_hl.email_list = get_data
    with pytest.raises(ValueError):
        main.write_output_data(get_inout_hl, tmpdir)

    # non-empty file, non-overwrite
    outpath = tmp_path / "test_output.csv"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write("test")
    with pytest.raises(ValueError):
        main.write_output_data(get_inout_hl, outpath)


def test_write_output_data_overwrite(get_data, tmp_path, get_inout_hl):
    # non-empty file, overwrite
    outpath = tmp_path / "test_output.csv"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write("test")
    get_inout_hl.email_list = get_data
    main.write_output_data(get_inout_hl, outpath, overwrite=True)
    with open(outpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 3  # header + 2 emails

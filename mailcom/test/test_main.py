import pytest
from mailcom import main
from mailcom import utils
from mailcom.inout import InoutHandler
import json
from pathlib import Path
from importlib import resources
import csv


def test_get_input_handler_csv_empty(tmp_path):
    inpath = tmp_path / "test.csv"
    with open(inpath, "w", newline="", encoding="utf-8"):
        pass  # empty file

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
    assert email["attachement type"] is None


def test_get_input_handler_dir(tmpdir):
    indir = tmpdir.join("sub")
    utils.make_dir(indir)
    with pytest.raises(ValueError):
        main.get_input_handler(indir, in_type="dir")


def test_is_valid_settings():
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


def test_get_workflow_settings_default():
    settings = main.get_workflow_settings()
    assert settings.get("default_lang") == "fr"

    settings = main.get_workflow_settings("default")
    assert settings.get("default_lang") == "fr"


def test_get_workflow_settings_file(tmp_path):
    setting_path = tmp_path / "settings.json"

    # invalid cases
    with pytest.warns(UserWarning):
        main.get_workflow_settings(setting_path)

    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        pass  # empty file
    with pytest.warns(UserWarning):
        main.get_workflow_settings(setting_path)

    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        f.write("test")
    with pytest.warns(UserWarning):
        main.get_workflow_settings(setting_path)

    settings = main.get_workflow_settings(setting_path)
    assert settings.get("default_lang") == "fr"

    # valid cases
    # TODO modify after adding the schema validation
    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        json.dump({"test": "test"}, f)
    assert main.get_workflow_settings(setting_path) == {"test": "test"}


def test_get_workflow_settings_new_settings(tmp_path):
    # TODO modify after adding the schema validation
    new_settings = {"default_lang": "es"}

    settings = main.get_workflow_settings(new_settings=new_settings)
    assert settings.get("default_lang") == "es"

    setting_path = tmp_path / "settings.json"
    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        json.dump({"default_lang": "fr"}, f)
    settings = main.get_workflow_settings(setting_path, new_settings=new_settings)
    assert settings.get("default_lang") == "es"

    new_settings = {"test": "test"}
    with pytest.warns(UserWarning):
        main.get_workflow_settings(setting_path, new_settings=new_settings)


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
            "attachement type": ["jpg"],
        },
    ]


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
    assert email_1.get("lang") == "fr"
    assert email_1.get("detected_datetime") == []
    assert (
        email_1.get("pseudo_content")
        == "Claude [email] viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au [location]"
    )

    assert email_2.get("cleaned_content") == email_2.get("content")
    assert email_2.get("lang") == "es"
    assert email_2.get("detected_datetime") == ["28.03.2025 a las 10:30"]
    assert (
        email_2.get("pseudo_content")
        == "Esta foto fue tomada por José el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )


def test_process_data_no_lang(get_data, get_settings, get_inout_hl):
    get_settings["default_lang"] = "de"
    get_inout_hl.email_list = get_data
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    emails = get_inout_hl.get_email_list()
    email_1 = next(emails)
    email_2 = next(emails)

    assert email_1.get("lang") == "de"
    assert (
        email_1.get("pseudo_content")
        == "Mika [email] viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au [location]"
    )

    assert email_2.get("lang") == "de"
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

    assert email_2.get("detected_datetime") is None
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

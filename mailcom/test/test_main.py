import pytest
from mailcom import main
from mailcom import utils
from mailcom.inout import InoutHandler
import json
from pathlib import Path
from importlib import resources


def test_get_input_handler_csv(tmp_path):
    inpath = tmp_path / "test.csv"
    with open(inpath, "w", newline="", encoding="utf-8"):
        pass  # empty file

    inout_hl = main.get_input_handler(inpath, in_type="csv")
    assert inout_hl.email_list == []


def test_get_input_handler_dir(tmpdir):
    indir = tmpdir.join("sub")
    utils.make_dir(indir)
    with pytest.raises(ValueError):
        main.get_input_handler(indir, in_type="dir")


def test_get_workflow_settings(tmp_path):
    setting_path = tmp_path / "settings.json"
    with pytest.raises(FileNotFoundError):
        main.get_workflow_settings(setting_path)

    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        pass  # empty file
    with pytest.raises(json.JSONDecodeError):
        main.get_workflow_settings(setting_path)

    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        f.write("test")
    with pytest.raises(json.JSONDecodeError):
        main.get_workflow_settings(setting_path)

    with open(setting_path, "w", newline="", encoding="utf-8") as f:
        json.dump({"test": "test"}, f)
    assert main.get_workflow_settings(setting_path) == {"test": "test"}


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
    get_settings["pseudonymize"]["default_lang"] = "de"
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
    get_settings["pseudonymize"]["datetime_detection"] = False
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
    get_settings["pseudonymize"]["pseudo_emailaddresses"] = False
    get_inout_hl.email_list = get_data
    main.process_data(get_inout_hl.get_email_list(), get_settings)

    email_1 = next(get_inout_hl.get_email_list())

    assert (
        email_1.get("pseudo_content")
        == "Claude (alice@gmail.com) viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au [location]"
    )


def test_process_data_no_ne(get_data, get_settings, get_inout_hl):
    get_settings["pseudonymize"]["pseudo_ne"] = False
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
    get_settings["pseudonymize"]["pseudo_numbers"] = False
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


def test_write_output_data_invalid(get_data, tmp_path, get_inout_hl):
    outpath = tmp_path / "test_output.txt"
    with pytest.raises(ValueError):
        main.write_output_data(get_inout_hl, outpath)

    outpath = tmp_path / "test_output.csv"
    with pytest.raises(ValueError):
        main.write_output_data(get_inout_hl, outpath)

    get_inout_hl.email_list = get_data
    with pytest.raises(ValueError):
        main.write_output_data(get_inout_hl, "")

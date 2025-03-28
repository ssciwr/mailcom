import pytest
from mailcom import main
from mailcom import utils
import json


def test_get_input_data_csv(tmp_path):
    inpath = tmp_path / "test.csv"
    with open(inpath, "w", newline="", encoding="utf-8") as f:
        pass  # empty file

    infile = main.get_input_data(inpath, in_type="csv")
    assert infile == []


def test_get_input_data_dir(tmpdir):
    indir = tmpdir.join("sub")
    utils.make_dir(indir)
    with pytest.raises(ValueError):
        main.get_input_data(indir, in_type="dir")


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
            "content": "Esta foto fue tomada el 28.03.2025 a las 10:30. "
            "Compruébelo en el archivo adjunto",
            "attachment": 1,
            "attachement type": ["jpg"],
        },
    ]


@pytest.fixture()
def get_settings():
    return {
        "pseudonymize": {
            "default_lang": "",
            "datetime_detection": True,
            "time_parsing": "strict",
            "pseudo_emailaddresses": True,
            "pseudo_ne": True,
            "pseudo_numbers": True,
        }
    }


def test_process_data_default(get_data, get_settings):
    pseudo_emails = main.process_data(get_data, get_settings)

    assert pseudo_emails[0].get("cleaned_content") == pseudo_emails[0].get("content")
    assert pseudo_emails[0].get("lang") == "fr"
    assert pseudo_emails[0].get("datetime") == []
    assert (
        pseudo_emails[0].get("pseudo_content")
        == "Claude [email] viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au [location]"
    )

    assert pseudo_emails[1].get("cleaned_content") == pseudo_emails[1].get("content")
    assert pseudo_emails[1].get("lang") == "es"
    assert pseudo_emails[1].get("datetime") == ["28.03.2025 a las 10:30"]
    assert (
        pseudo_emails[1].get("pseudo_content")
        == "Esta foto fue tomada el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )


def test_process_data_no_lang(get_data, get_settings):
    get_settings["pseudonymize"]["default_lang"] = "de"
    pseudo_emails = main.process_data(get_data, get_settings)

    assert pseudo_emails[0].get("lang") == "de"
    assert (
        pseudo_emails[0].get("pseudo_content")
        == "Claude [email] viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au [location]"
    )

    assert pseudo_emails[1].get("lang") == "de"
    assert (
        pseudo_emails[1].get("pseudo_content")
        == "Esta foto fue tomada el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )


def test_process_data_no_datetime(get_data, get_settings):
    get_settings["pseudonymize"]["datetime_detection"] = False
    pseudo_emails = main.process_data(get_data, get_settings)

    assert pseudo_emails[1].get("datetime") == None
    assert (
        pseudo_emails[1].get("pseudo_content")
        == "Esta foto fue tomada el [number].[number].[number] a las [number]:[number]. "
        "Compruébelo en el archivo adjunto"
    )


def test_process_data_no_email(get_data, get_settings):
    get_settings["pseudonymize"]["pseudo_emailaddresses"] = False
    pseudo_emails = main.process_data(get_data, get_settings)

    assert (
        pseudo_emails[0].get("pseudo_content")
        == "Claude (alice@gmail.com) viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au [location]"
    )


def test_process_data_no_ne(get_data, get_settings):
    get_settings["pseudonymize"]["pseudo_ne"] = False
    pseudo_emails = main.process_data(get_data, get_settings)

    assert (
        pseudo_emails[0].get("pseudo_content")
        == "Alice [email] viendra au bâtiment à [number]h[number]. "
        "Nous nous rendrons ensuite au MeetingPoint"
    )


def test_process_data_no_numbers(get_data, get_settings):
    get_settings["pseudonymize"]["pseudo_numbers"] = False
    pseudo_emails = main.process_data(get_data, get_settings)

    assert (
        pseudo_emails[0].get("pseudo_content")
        == "Claude [email] viendra au bâtiment à 10h00. "
        "Nous nous rendrons ensuite au [location]"
    )

    assert (
        pseudo_emails[1].get("pseudo_content")
        == "Esta foto fue tomada el 28.03.2025 a las 10:30. "
        "Compruébelo en el archivo adjunto"
    )

from pathlib import Path
from mailcom.inout import InoutHandler, load_csv
from mailcom import utils
from mailcom.lang_detector import LangDetector
from mailcom.time_detector import TimeDetector
from mailcom.parse import Pseudonymize
import json


def get_input(in_path: str, in_type: str = "dir") -> list[dict]:
    """Get input data from a file or directory.

    Args:
        in_path (str): The path to the input data.
        in_type (str, optional): The type of input data. Defaults to "dir".
            Possible values are "dir" and "csv".

    Returns:
        list[dict]: The list of dictionaries containing the input data.
            "content" field in each dictionary contains the main content.
    """
    if in_type == "csv":
        return load_csv(in_path)
    else:
        inout = InoutHandler(in_path)
        inout.list_of_files()
        inout.process_emails()
        return inout.get_email_list()


def get_workflow_settings(workflow_settings: str) -> dict:
    """Get the workflow settings from a file.

    Args:
        workflow_settings (str): Path to the workflow settings file.

    Returns:
        dict: The workflow settings.
    """
    try:
        with open(workflow_settings, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(
            "Workflow settings file not found: {}".format(workflow_settings)
        )
    except json.JSONDecodeError:
        raise json.JSONDecodeError(
            "Error decoding JSON file: {}".format(workflow_settings)
        )


def process_data(email_list: list[dict], workflow_settings: str) -> list[dict]:
    """Process the input data in this order:
    + detect language (optional)
    + detect date time (optional)
    + pseudonymize email addresses (optional)
    + pseudoymize name entities
    + pseudonymize numbers (optional)

    Args:
        email_list (list[dict]): The list of dictionaries containing the input data.
        "content" field in each dictionary contains the main content.
        workflow_settings (str): Path to the workflow settings file.

    Returns:
        list[dict]: The list of dictionaries containing the processed data.
    """
    # get workflow settings
    settings = get_workflow_settings(workflow_settings)
    lang = settings["pseudonymize"]["default_lang"]
    detect_lang = True if lang else False
    detect_datetime = settings["pseudonymize"]["datetime_detection"]
    pseudo_emailaddresses = settings["pseudonymize"]["pseudo_emailaddresses"]
    pseudo_numbers = settings["pseudonymize"]["pseudo_numbers"]

    # init necessary objects
    spacy_loader = utils.SpacyLoader()
    trans_loader = utils.TransformerLoader()
    pseudonymizer = Pseudonymize(trans_loader, spacy_loader)
    if detect_lang:
        lang_detector = LangDetector(trans_loader)
    if detect_datetime:
        parsing_type = settings["pseudonymize"]["time_parsing"]
        time_detector = TimeDetector(parsing_type, spacy_loader)

    for email in email_list:
        if detect_lang:
            lang = lang_detector.get_detections(
                email["content"], lang_lib="langid", pipeline_info=None
            )
            email["lang"] = lang
        if detect_datetime:
            detected_time = time_detector.get_date_time(
                email["content"], lang, model="default"
            )
            email["datetime"] = [
                item[0] for item in detected_time
            ]  # only keep the strings
        pseudo_content = pseudonymizer.pseudonymize(
            email["content"],
            lang,
            model="default",
            pipeline_info=None,
            detected_dates=email.get("datetime", None),
            pseudo_emailaddresses=pseudo_emailaddresses,
            pseudo_numbers=pseudo_numbers,
        )
        email["pseudo_content"] = pseudo_content

    return email_list

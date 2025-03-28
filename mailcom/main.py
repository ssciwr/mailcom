from pathlib import Path
from mailcom.inout import InoutHandler, load_csv
from mailcom import utils
from mailcom.lang_detector import LangDetector
from mailcom.time_detector import TimeDetector
from mailcom.parse import Pseudonymize
import json


def get_input_data(
    in_path: str,
    in_type: str = "dir",
    col_name: str = "message",
    file_types: list = [".eml", ".html"],
) -> list[dict]:
    """Get input data from a file or directory.

    Args:
        in_path (str): The path to the input data.
        in_type (str, optional): The type of input data. Defaults to "dir".
            Possible values are ["dir", "csv"].
        col_name (str, optional): The name of the column containing
            the main content in csv file-
            Defaults to "message".
        file_types (list, optional): The list of file types
            to be processed in the directory.
            Defaults to [".eml", ".html"].

    Returns:
        list[dict]: The list of dictionaries containing the input data.
            "content" field in each dictionary contains the main content.
    """
    if in_type == "csv":
        return load_csv(in_path, col_name)
    else:
        inout = InoutHandler(in_path, file_types)
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
            "Error reading workflow settings file: {}".format(workflow_settings),
            doc="",
            pos=0,
        )


def process_data(email_list: list[dict], workflow_settings: dict) -> list[dict]:
    """Process the input data in this order:
    + detect language (optional)
    + detect date time (optional)
    + pseudonymize email addresses (optional)
    + pseudoymize name entities
    + pseudonymize numbers (optional)

    Args:
        email_list (list[dict]): The list of dictionaries containing the input data.
        "content" field in each dictionary contains the main content.
        workflow_settings (dict): The workflow settings.

    Returns:
        list[dict]: The list of dictionaries containing the processed data.
    """
    # get workflow settings
    settings = workflow_settings.get("pseudonymize", {})
    lang = settings.get("default_lang", "")
    detect_lang = False if lang else True
    detect_datetime = settings.get("datetime_detection", True)
    pseudo_emailaddresses = settings.get("pseudo_emailaddresses", True)
    pseudo_ne = settings.get("pseudo_ne", True)
    pseudo_numbers = settings.get("pseudo_numbers", True)

    # init necessary objects
    spacy_loader = utils.SpacyLoader()
    trans_loader = utils.TransformerLoader()
    pseudonymizer = Pseudonymize(trans_loader, spacy_loader)
    if detect_lang:
        lang_detector = LangDetector(trans_loader)
    if detect_datetime:
        parsing_type = settings.get("time_parsing", "strict")
        time_detector = TimeDetector(parsing_type, spacy_loader)

    for email in email_list:
        email_content, _ = utils.clean_up_content(email["content"])
        email["cleaned_content"] = email_content

        if detect_lang:
            det_langs = lang_detector.get_detections(
                email_content, lang_lib="langid", pipeline_info=None
            )
            lang = det_langs[0][0]  # first detected lang, no prob.
        email["lang"] = lang

        if detect_datetime:
            detected_time = time_detector.get_date_time(
                email_content, lang, model="default"
            )
            email["datetime"] = [
                item[0] for item in detected_time
            ]  # only keep the strings

        pseudo_content = pseudonymizer.pseudonymize(
            email_content,
            lang,
            model="default",
            pipeline_info=None,
            detected_dates=email.get("datetime", None),
            pseudo_emailaddresses=pseudo_emailaddresses,
            pseudo_ne=pseudo_ne,
            pseudo_numbers=pseudo_numbers,
        )
        email["pseudo_content"] = pseudo_content

    return email_list


def write_output_data(email_list: list[dict], out_path: str):
    """Write the output data to a file.

    Args:
        email_list (list[dict]): The list of dictionaries containing the processed data.
        out_path (str): The path to the output file.
    """
    pass

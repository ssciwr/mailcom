from pathlib import Path
from mailcom.inout import InoutHandler
from mailcom import utils
from mailcom.lang_detector import LangDetector
from mailcom.time_detector import TimeDetector
from mailcom.parse import Pseudonymize
import json
from collections.abc import Iterator
from importlib import resources
import jsonschema


def get_input_handler(
    in_path: str,
    in_type: str = "dir",
    col_names: list = ["message"],
    init_data_fields: list = ["content", "date", "attachment", "attachement type"],
    unmatched_keyword: str = "unmatched",
    file_types: list = [".eml", ".html"],
) -> InoutHandler:
    """Get input handler for a file or directory.

    Args:
        in_path (str): The path to the input data.
        in_type (str, optional): The type of input data. Defaults to "dir".
            Possible values are ["dir", "csv"].
        col_names (list, optional): The list of column names that
            map the init_data_fields.
        init_data_fields (list, optional): The list of fields
            should be present in the data dict.
        unmatched_keyword (str, optional): The keyword for
            marking unmatch columns in csv files.
            Defaults to "unmatched".
        file_types (list, optional): The list of file types
            to be processed in the directory.
            Defaults to [".eml", ".html"].

    Returns:
        InoutHandler: The input handler object.
    """
    inout_handler = InoutHandler(init_data_fields)
    if in_type == "csv":
        inout_handler.load_csv(in_path, col_names, unmatched_keyword)
    else:
        inout_handler.list_of_files(in_path, file_types)
        inout_handler.process_emails()
    return inout_handler


def is_valid_settings(workflow_setting: dict) -> bool:
    """Check if the workflow settings are valid.
    Args:
        workflow_setting (dict): The workflow settings.

    Returns:
        bool: True if the settings are valid, False otherwise.
    """
    pkg = resources.files("mailcom")
    setting_schema_path = Path(pkg / "setting_schema.json")
    setting_schema = json.load(open(setting_schema_path, "r", encoding="utf-8"))

    try:
        jsonschema.validate(instance=workflow_setting, schema=setting_schema)
        return True
    except jsonschema.ValidationError:
        return False


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


def process_data(email_list: Iterator[list[dict]], workflow_settings: dict):
    """Process the input data in this order:
    + detect language (optional)
    + detect date time (optional)
    + pseudonymize email addresses (optional)
    + pseudoymize name entities
    + pseudonymize numbers (optional)

    Args:
        email_list (Iterator[list[dict]]): The list of dictionaries of input data.
        "content" field in each dictionary contains the main content.
        workflow_settings (dict): The workflow settings.
    """
    # get workflow settings
    unmatched_keyword = workflow_settings.get("unmatched_keyword", "unmatched")
    lang = workflow_settings.get("default_lang", "")
    detect_lang = False if lang else True
    detect_datetime = workflow_settings.get("datetime_detection", True)
    pseudo_emailaddresses = workflow_settings.get("pseudo_emailaddresses", True)
    pseudo_ne = workflow_settings.get("pseudo_ne", True)
    pseudo_numbers = workflow_settings.get("pseudo_numbers", True)
    pseudo_first_names = workflow_settings.get("pseudo_first_names", {})
    lang_lib = workflow_settings.get("lang_detection_lib", "langid")
    lang_pipeline = workflow_settings.get("lang_pipeline", None)
    spacy_model = workflow_settings.get("spacy_model", "default")
    ner_pipeline = workflow_settings.get("ner_pipeline", None)

    # init necessary objects
    spacy_loader = utils.SpacyLoader()
    trans_loader = utils.TransformerLoader()
    pseudonymizer = Pseudonymize(pseudo_first_names, trans_loader, spacy_loader)
    if detect_lang:
        lang_detector = LangDetector(trans_loader)
    if detect_datetime:
        parsing_type = workflow_settings.get("time_parsing", "strict")
        time_detector = TimeDetector(parsing_type, spacy_loader)

    for email in email_list:
        # skip if email content is empty or not present
        if not email.get("content") or email.get("content") == unmatched_keyword:
            continue

        email_content, _ = utils.clean_up_content(email["content"])
        email["cleaned_content"] = email_content

        if detect_lang:
            det_langs = lang_detector.get_detections(
                email_content, lang_lib=lang_lib, pipeline_info=lang_pipeline
            )
            lang = det_langs[0][0]  # first detected lang, no prob.
        email["lang"] = lang

        if detect_datetime:
            detected_time = time_detector.get_date_time(
                email_content, lang, model=spacy_model
            )
            email["detected_datetime"] = [
                item[0] for item in detected_time
            ]  # only keep the strings

        pseudo_content = pseudonymizer.pseudonymize(
            email_content,
            lang,
            model=spacy_model,
            pipeline_info=ner_pipeline,
            detected_dates=email.get("detected_datetime", None),
            pseudo_emailaddresses=pseudo_emailaddresses,
            pseudo_ne=pseudo_ne,
            pseudo_numbers=pseudo_numbers,
        )
        email["pseudo_content"] = pseudo_content
        email["ne_list"] = pseudonymizer.ne_list


def write_output_data(inout_hl: InoutHandler, out_path: str, overwrite: bool = False):
    """Write the output data to a file.

    Args:
        inout_hl (InoutHandler): The input handler object containing the data.
        out_path (str): The path to the output file.
        overwrite (bool, optional): Flag to overwrite the output file if it exists.
            Defaults to False.
    """
    if not out_path:
        raise ValueError("No output path specified")

    # check if the output file is not empty
    if Path(out_path).is_file() and Path(out_path).stat().st_size > 0 and not overwrite:
        raise ValueError("Output file is not empty")

    file_type = Path(out_path).suffix[1:]

    if file_type == "csv":
        inout_hl.write_csv(out_path)
    elif file_type == "xml":
        xml = inout_hl.data_to_xml()
        inout_hl.write_file(xml, out_path)
    else:
        raise ValueError("Invalid file type: {}".format(file_type))

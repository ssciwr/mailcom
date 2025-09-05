from pathlib import Path
from importlib import resources
from mailcom.inout import InoutHandler
from mailcom import utils
from mailcom.lang_detector import LangDetector
from mailcom.time_detector import TimeDetector
from mailcom.parse import Pseudonymize
import json
from collections.abc import Iterator
import jsonschema
import warnings
from datetime import datetime
import socket
import copy


def get_input_handler(
    in_path: str,
    in_type: str = "dir",
    col_names: list = ["message"],
    init_data_fields: list = [
        "content",
        "date",
        "attachment",
        "attachement type",
        "subject",
    ],
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


def _update_new_settings(workflow_settings: dict, new_settings: dict) -> bool:
    """Update the workflow settings directly with the new settings.

    Args:
        workflow_settings (dict): The workflow settings.
        new_settings (dict): The new settings.

    Returns:
        bool: True if the settings are updated, False otherwise.
    """
    updated = False
    if not workflow_settings:
        raise ValueError("Workflow settings are empty")

    for key, new_value in new_settings.items():
        # check if the new value is different from the old value
        # if the setting schema has more nested structures, deepdiff should be used
        # here just simple check
        updatable = (
            key in workflow_settings
            and workflow_settings[key] != new_value
            and is_valid_settings({key: new_settings[key]})
        )
        if key not in workflow_settings:
            warnings.warn(
                "Key {} not found in the workflow settings "
                "and will be skipped.".format(key),
                UserWarning,
            )
        if key in workflow_settings and not is_valid_settings({key: new_settings[key]}):
            warnings.warn(
                "Value of key {} is not valid in the workflow settings "
                "and will be skipped.".format(key),
                UserWarning,
            )
        if updatable:
            workflow_settings[key] = new_value
            updated = True

    return updated


def save_settings_to_file(workflow_settings: dict, dir_path: str = None):
    """Save the workflow settings to a file.
    If dir_path is None, save to the current directory.

    Args:
        workflow_settings (dict): The workflow settings.
        dir_path (str, optional): The path to save the settings file.
            Defaults to None.
    """
    now = datetime.now()
    timestamp = (
        now.strftime("%Y%m%d_%H%M%S.") + now.strftime("%f")[:3]
    )  # first 3 digits of milliseconds
    hostname = socket.gethostname()
    file_name = "updated_workflow_settings_{}_{}.json".format(timestamp, hostname)
    file_path = ""

    if dir_path is None:
        file_path = Path.cwd() / file_name
    else:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            file_path = Path(dir_path) / file_name
        except FileExistsError:
            raise ValueError(
                "The path {} already exists and is not a directory".format(dir_path)
            )

    # save the settings to a file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(workflow_settings, f, indent=4, ensure_ascii=False)

    print("The workflow settings have been saved to {}".format(file_path))


def get_workflow_settings(
    setting_path: str = "default",
    new_settings: dict = {},
    updated_setting_dir: str = None,
    save_updated_settings: bool = True,
) -> dict:
    """Get the workflow settings.
    If the setting path is "default", return the default settings.
    If the setting path is not default, read the settings from the file.
    If the new settings are provided, overwrite the default/loaded settings.

    Args:
        setting_path (str): Path to the workflow settings file.
            Defaults to "default".
        new_settings (dict): New settings to overwrite the existing settings.
            Defaults to {}.
        updated_setting_dir (str): Directory to save the updated settings file.
            Defaults to None.
        save_updated_settings (bool): Whether to save the updated settings to a file.

    Returns:
        dict: The workflow settings.
    """
    workflow_settings = {}
    pkg = resources.files("mailcom")
    default_setting_path = Path(pkg / "default_settings.json")

    def load_json(file_path: Path) -> dict:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    try:
        workflow_settings = (
            load_json(default_setting_path)
            if setting_path == "default"
            else load_json(Path(setting_path))
        )
        if setting_path != "default" and not is_valid_settings(workflow_settings):
            warnings.warn(
                "Invalid workflow settings file. Using default settings instead.",
                UserWarning,
            )
            workflow_settings = load_json(default_setting_path)
    except Exception:
        warnings.warn(
            "Error in loading the workflow settings file. "
            "Using default settings instead.",
            UserWarning,
        )
        workflow_settings = load_json(default_setting_path)

    # update the workflow settings with the new settings
    updated = _update_new_settings(workflow_settings, new_settings)

    if updated and save_updated_settings:
        save_settings_to_file(workflow_settings, updated_setting_dir)

    return workflow_settings


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
        exclude_pseudonym = False
        pseudo_content, exclude_pseudonym = pseudonymizer.pseudonymize(
            email_content,
            lang,
            model=spacy_model,
            pipeline_info=ner_pipeline,
            detected_dates=email.get("detected_datetime", None),
            pseudo_emailaddresses=pseudo_emailaddresses,
            pseudo_ne=pseudo_ne,
            pseudo_numbers=pseudo_numbers,
        )
        # make sure ne pseudonymization is restarted in case of
        # matching pseudonym
        # note that the matching pseudonym is subsequently excluded
        # from all further processing but will be present in the initial
        # data entries
        pseudo_content, _ = pseudonymizer.pseudonymize_with_updated_ne(
            copy.deepcopy(pseudonymizer.sentences),
            None,
            language=lang,
            detected_dates=email.get("detected_datetime", None),
            pseudo_emailaddresses=pseudo_emailaddresses,
            pseudo_ne=pseudo_ne,
            pseudo_numbers=pseudo_numbers,
        )
        # use deepcopy to avoid issue with mutable objects
        email["pseudo_content"] = pseudo_content
        email["ne_list"] = copy.deepcopy(pseudonymizer.ne_list)
        # remove score from the list
        for ne in email["ne_list"]:
            ne.pop("score")
        email["ne_sent"] = copy.deepcopy(pseudonymizer.ne_sent)
        email["sentences"] = copy.deepcopy(pseudonymizer.sentences)

        # record sentences after email pseudonymization
        if pseudo_emailaddresses:
            email["sentences_after_email"] = [
                pseudonymizer.pseudonymize_email_addresses(sent)
                for sent in email["sentences"]
            ]


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

from importlib import metadata
from mailcom.main import (
    get_input_handler,
    get_workflow_settings,
    process_data,
    write_output_data,
)
from mailcom.utils import highlight_ne_sent

__version__ = metadata.version("mailcom")

__all__ = [
    "get_input_handler",
    "get_workflow_settings",
    "process_data",
    "write_output_data",
    "highlight_ne_sent",
]

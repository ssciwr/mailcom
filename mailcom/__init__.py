try:
    from importlib import metadata
except ImportError:
    # Running on pre-3.8 Python; use importlib-metadata package
    import importlib_metadata as metadata  # type: ignore
from mailcom.main import (
    get_input_handler,
    get_workflow_settings,
    process_data,
    write_output_data,
)


__version__ = metadata.version("mailcom")

__all__ = [
    "get_input_handler",
    "get_workflow_settings",
    "process_data",
    "write_output_data",
]

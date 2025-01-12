from pathlib import Path
import os
import eml_parser
from bs4 import BeautifulSoup
from dicttoxml import dicttoxml


class InoutHandler:
    def __init__(self, directory_name: str):
        """Constructor for the InoutHandler class.

        Args:
            directory_name (str): The directory where the files are located.
        """
        self.directory_name = directory_name
        # presets
        self.pattern = [".eml", ".html"]

    def list_of_files(self):
        """Method to create a list of Path objects (files) that are present
        in a directory."""
        if not os.path.exists(
            self.directory_name
        ):  # check if given dir exists raises error otherwise
            raise OSError("Path {} does not exist".format(self.directory_name))
        mypath = Path(self.directory_name)
        self.email_list = [
            mp.resolve() for mp in mypath.glob("**/*") if mp.suffix in self.pattern
        ]
        if len(self.email_list) == 0:
            raise ValueError(
                """The directory {} does not contain .eml or .html files.
                Please check that the directory is containing the email
                data files""".format(
                    mypath
                )
            )

    def get_html_text(self, text_check: str) -> str:
        """Clean up a string if it contains html content.
        Args:
            text_check (str): The string that may contain html content.

        Returns:
            str: The (potentially) cleaned up string."""
        soup = BeautifulSoup(text_check, "html.parser")
        if soup.find():
            text_check = soup.get_text()
        return text_check

    def get_text(self, file: Path) -> str:
        """Function to extract the textual content and other metadata from an email file.

        Args:
            file (Path): The path to the email file.

        Returns:
            str: The textual content of the email. In the future, this will return the
            complete dictionary with the metadata."""
        if not file.is_file():  # check if given file exists raises error otherwise
            raise OSError("File {} does not exist".format(file))
        with open(file, "rb") as fhdl:
            raw_email = fhdl.read()
        ep = eml_parser.EmlParser(include_raw_body=True)
        parsed_eml = ep.decode_email_bytes(raw_email)
        attachmenttypes = []
        # find if there are any attachements, and if yes, how many
        attachments = len(parsed_eml["attachment"]) if "attachment" in parsed_eml else 0
        # find the types of attachements
        if attachments > 0:
            attachmenttypes = [
                parsed_eml["attachment"][i]["extension"] for i in range(attachments)
            ]
        self.email_content = {
            "content": parsed_eml["body"][0]["content"],
            "date": parsed_eml["header"]["date"],
            "attachment": attachments,
            "attachement type": attachmenttypes,
        }
        return self.email_content["content"]

    def validate_data(self):
        pass

    def data_to_xml(self, text):
        def my_item_func(x):
            return "content"

        xml = dicttoxml(text, custom_root="email", item_func=my_item_func)
        return xml.decode()

    def write_file(self, text: str, name: str) -> None:
        """Write the extracted string to a text file.

        Args:
            text (str): The string to be written to the file.
            name (str): The name of the file to be written."""
        with open("{}.out".format(name), "w") as file:
            file.write(text)

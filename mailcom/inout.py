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

        # list containing all emails
        self.email_list = []

    def list_of_files(self):
        """Method to create a list of Path objects (files) that are present
        in a directory."""
        if not os.path.exists(
            self.directory_name
        ):  # check if given dir exists raises error otherwise
            raise OSError("Path {} does not exist".format(self.directory_name))
        mypath = Path(self.directory_name)
        self.email_path_list = [
            mp.resolve() for mp in mypath.glob("**/*") if mp.suffix in self.pattern
        ]
        if len(self.email_path_list) == 0:
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

    def extract_email_info(self, file: Path) -> dict:
        """Function to extract the textual content and other metadata
        from a single email file.

        Args:
            file (Path): The path to the email file.

        Returns:
            dict: Dictionary containing email text and metadata."""
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
        email_content = {
            "content": parsed_eml["body"][0]["content"],
            "date": parsed_eml["header"]["date"],
            "attachment": attachments,
            "attachement type": attachmenttypes,
        }
        # clean up html content
        email_content["content"] = self.get_html_text(email_content["content"])

        return email_content

    def process_emails(self):
        """Function that processes all emails in the directory
        and saves their contents in email_list"""

        for email_path in self.email_path_list:
            print("Processing input file {}".format(email_path))
            email_dict = self.extract_email_info(email_path)
            self.email_list.append(email_dict)

    def get_email_list(self):
        """Function that returns an iterator of email_list

        Returns:
            iter: Iterator of self.email_list."""
        return iter(self.email_list)

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

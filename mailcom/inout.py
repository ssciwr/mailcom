from pathlib import Path
import os
import eml_parser
from bs4 import BeautifulSoup

class InoutHandler:
    @staticmethod
    def list_of_files(directory_name: str) -> list[Path]:
        """Function to create a list of files that are present in a directory as path objects.
        
        Args: 
            directory_name (str): The directory where the files are located.
        
        Returns:
            list[Path]: A list of Path objects that represent the files in the directory."""
        if not os.path.exists(directory_name): # check if given dir exists raises error otherwise
            raise OSError("Path {} does not exist".format(directory_name))
        mypath = Path(directory_name)
        pattern = [".eml", ".html"]  # we would not change the file type through user input
        email_list = [mp.resolve() for mp in mypath.glob("**/*") if mp.suffix in pattern]
        if len(email_list) == 0:
            raise ValueError("The directory {} does not contain .eml or .html files. Please check that the directory is containing the email data files".format(mypath))
        return email_list

    @staticmethod
    def get_html_text(text_check: str) -> str:
        """Clean up a string if it contains html content.
        Args:
            text_check (str): The string that may contain html content.
            
        Returns:
            str: The (potentially) cleaned up string."""
        soup = BeautifulSoup(text_check , 'html.parser')
        if soup.find():
            text_check = soup.get_text()
        return text_check

    @staticmethod
    def get_text(file: Path) -> str:
        """Function to extract the textual content and other metadata from an email file.
        
        Args:
            file (Path): The path to the email file.
            
        Returns:
            str: The textual content of the email. In the future, this will return the 
            complete dictionary with the metadata."""
        if not file.is_file(): # check if given file exists raises error otherwise
            raise OSError("File {} does not exist".format(file))
        with open(file, 'rb') as fhdl:
            raw_email = fhdl.read()
        ep = eml_parser.EmlParser(include_raw_body=True)
        parsed_eml = ep.decode_email_bytes(raw_email)
        attachmenttypes = []
        # find if there are any attachements, and if yes, how many
        attachments = len(parsed_eml["attachment"]) if "attachment" in parsed_eml else 0
        # find the types of attachements
        if attachments > 0:
            attachmenttypes = [parsed_eml["attachment"][i]["extension"] for i in range(attachments)]
        email_content = {"content": parsed_eml["body"][0]["content"], 
                    "date": parsed_eml["header"]["date"], 
                    "attachment": attachments, 
                    "attachement type": attachmenttypes
                    }
        return(email_content["content"])

    def validate_data():
        return
    
    def data_to_xml():
        return

def write_file(text: str, name: str)-> None:
    """Write the extracted string to a text file.
    
    Args:
        text (str): The string to be written to the file.
        name (str): The name of the file to be written."""
    with open("{}.out".format(name), "w") as file:
        file.write(text)

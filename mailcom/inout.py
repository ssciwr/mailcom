from pathlib import Path
import os
import eml_parser
from bs4 import BeautifulSoup

def list_of_files(directory_name: str) -> list[Path]:
    if not os.path.exists(directory_name): # check if given dir exists raises error otherwise
        raise OSError("Path {} does not exist".format(directory_name))
    mypath = Path(directory_name)
    pattern = [".eml", ".html"]  # we would not change the file type through user input
    email_list = [mp.resolve() for mp in mypath.glob("**/*") if mp.suffix in pattern]
    if len(email_list) == 0:
        raise ValueError("The directory {} does not contain .eml or .html files. Please check that the directory is containing the email data files".format(mypath))
    return email_list

def get_html_text(text_check):
    soup = BeautifulSoup(text_check , 'html.parser')
    if soup.find():
        text = soup.get_text()
        return text
    return text_check

def get_text(file):
    if not file.is_file(): # check if given file exists raises error otherwise
        raise OSError("File {} does not exist".format(file))
    with open(file, 'rb') as fhdl:
        raw_email = fhdl.read()
    ep = eml_parser.EmlParser(include_raw_body=True)
    parsed_eml = ep.decode_email_bytes(raw_email)
    attachments = 0
    attachmenttypes = []
    if "attachment" in parsed_eml:
        attachments = len(parsed_eml["attachment"])
        if attachments > 0:
            for i in range(attachments):
                attachmenttypes.append(parsed_eml["attachment"][i]["extension"])
        
    email_content = {"content": parsed_eml["body"][0]["content"], 
                 "date": parsed_eml["header"]["date"], 
                 "attachment": attachments, 
                 "attachement type": attachmenttypes
                 }
    return(email_content["content"])


def write_file(text, name):
    with open("{}.out".format(name), "w") as file:
        file.write(text)

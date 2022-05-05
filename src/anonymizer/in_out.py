import os
from email import policy
from email.parser import BytesHeaderParser, BytesParser

path = './data/'

def list_of_files(path):
    """Get all the eml files in the directory and put them in a list."""
    email_list = [f for f in os.listdir(path) if f.endswith('.eml')]
    return email_list

def get_text(name):
    with open(name, 'rb') as fp:
        msg = BytesParser(policy=policy.default).parse(fp)
    return msg.get_body(preferencelist='plain').get_content()

def delete_header(text):
    items_to_delete = ["Von:", "Gesendet:", "Betreff:", "An:", "Cc:",
                       "Sujet", "Date", "De", "Pour", "Copie "]
    lines_to_delete = []
    text_out_list = text.splitlines()
    for index, line in enumerate(text_out_list):
        if any(i in items_to_delete for i in line.strip().split(" ")):
            lines_to_delete.append(index)
            # print("Deleting {}".format(line))
    # delete lines
    for i in reversed(lines_to_delete):
        # print("xxxxx {}".format(text_out_list[i]))
        del text_out_list[i]
    return " ".join(text_out_list)

def write_file(text, name):
    with open("{}.out".format(name), "w") as file:
        file.write(text)

if __name__ == "__main__":
    eml_files = list_of_files(path)
    print("Found files: {}".format(eml_files))
    for file in eml_files:
        text = get_text(path+file)
        text = delete_header(text)
        # still need to delete email addresses in "blabla wrote:"
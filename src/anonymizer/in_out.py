import os
import email
from email import policy
from email.parser import BytesHeaderParser, BytesParser

path = './data/test/'

def list_of_files(path):
    """Get all the eml files in the directory and put them in a list."""
    email_list = [f for f in os.listdir(path) if f.endswith('.eml')]
    return email_list

def delete_header(text):
    items_to_delete = ["Von:", "Gesendet:", "Betreff:", "An:", "Cc:"]
    for line in text.splitlines():
        # print([i in items_to_delete for i in line.strip().split(" ")])
        if not any(i in items_to_delete for i in line.strip().split(" ")):
            print(line)

def write_file(text, name):
    with open("{}.out".format(name), "w") as file:
        file.write(text)
        fp.close()

if __name__ == "__main__":
    eml_files = list_of_files(path)
    print("Found files: {}".format(eml_files))
    for file in eml_files:
        with open(path+file, 'rb') as fp:
            msg = BytesParser(policy=policy.default).parse(fp)
            fp.close()
            text = msg.get_body(preferencelist='plain').get_content()
            # print(text)
            delete_header(text)
            exit()
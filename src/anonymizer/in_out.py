import os
import email
from email import policy
from email.parser import BytesHeaderParser, BytesParser
from cv2 import fillPoly
import pandas as pd

def list_of_files(path):
    """Get all the eml files in the directory and put them in a list."""
    email_list = [f for f in os.listdir(path) if f.endswith('.eml')]
    return email_list

path = './data/'
eml_files = list_of_files(path)

print("Found files: {}".format(eml_files))

keys_to_delete = ["From", "To", "Date", "Subject"]
for file in eml_files:
    with open(path+file, 'rb') as fp:
        name = fp.name  
        msg = BytesParser(policy=policy.default).parse(fp)
        # clean the header information
        for mykey in keys_to_delete:
            if mykey not in msg.keys():
                print("Could not delete key {}".format(mykey))
                print("Not one of {}".format(msg.keys()))
            msg.__delitem__(mykey)
        text = msg.get_body(preferencelist='plain').get_content()
        print(text)
        with open("{}.out".format(name), "w") as file:
            file.write(text)
    fp.close()

# df_eml = pd.DataFrame([file_names, texts]).T
# df_eml.columns = ['file_name', 'text']
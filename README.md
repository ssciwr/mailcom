# anonymize
Tool to remove header, names and main email body from email text, except salutation and closing. Reads in email files in eml format and writes to xml including metadata, which can be imported into a corpus database.

So far, this takes the email body and retains only the salutation, with names removed, for French of Spanish emails.

To retain also the ending of the email, more homogeneous sample data is required. 
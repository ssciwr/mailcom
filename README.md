# mailcom
Tool to parse email body from email text (eml file), and retains only the text, with names removed, for French of Spanish emails.

# Installation
Install using  
`python -m pip install mailcom`

You will also need to download the French and Spanish models for spaCy and Stanza using the provided script - run this in the terminal:

`./get-models.sh`

For an overview over the available languages and models, check the [spaCy](https://spacy.io/usage/models) website.

# Usage
The package uses spaCy for sentencizing, based on the default language models, and transformers for NER recognition.
Currently, you have to set the language and eml file directory manually at the top of `parse.py`; the default directory is `data/in`. Then run `python parse.py`. After the run, the output can be found in `data/out`.

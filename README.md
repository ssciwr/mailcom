# anonymize
Tool to parse email body from email text (eml file), and retains only the salutation, with names removed, for French of Spanish emails.

# Installation
First you need to install [spaCy](https://spacy.io/) and [Stanza](https://stanfordnlp.github.io/stanza/) through  
`python -m pip install -r requirements.txt`

You will also need to download the French and Spanish models for spaCy and Stanza using the provided script - run this in the terminal:

`./get-models.sh`

For an overview over the available languages and models, check the [spaCy](https://spacy.io/usage/models) and [Stanza](https://stanfordnlp.github.io/stanza/available_models.html) websites.

# Usage
The package uses spaCy for sentencizing, based on the default language models, and Stanza for NER recognition, using the NER wikiNER model for French and CoNLL02 model for Spanish.
Currently, you have to set the language and eml file directory manually at the top of `parse.py`; the default directory is `data/`. Then run `python parse.py`. After the run, the output can be found in `data/out`.

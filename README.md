# mailcom: pseudonimization tool for textual data
![License: MIT](https://img.shields.io/github/license/ssciwr/mailcom)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/ssciwr/mailcom/ci.yml?branch=main)
![codecov](https://img.shields.io/codecov/c/github/ssciwr/mailcom)
![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ssciwr_mailcom&metric=alert_status)
![Language](https://img.shields.io/github/languages/top/ssciwr/mailcom)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ssciwr/mailcom/blob/main/docs/source/notebooks/demo.ipynb)

Tool to parse email body from email text (eml or html file) or csv file, and retain only the text, with names removed. By default for French, Spanish and Portuguese, but can easily be adapted to further languages with the help of configuration files.

# Installation
Create a Python virtual environment, ie. conda. Install `mailcom` into the environment using  
`python -m pip install mailcom`

For an overview over the available languages and models, check the [spaCy](https://spacy.io/usage/models) website. These models are used to sentencize the text, which is important for the subsequent `transformers` pipeline that carries out the Named Entity Recognition.

# Usage

The package can be configured using the configuration file, for an example see [here](mailcom/default_settings.json). The configuration options are:

keyword | option
----------------
"datetime_detection" | true 

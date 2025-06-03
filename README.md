# mailcom: pseudonimization tool for textual data
![License: MIT](https://img.shields.io/github/license/ssciwr/mailcom)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/ssciwr/mailcom/ci.yml?branch=main)
![codecov](https://img.shields.io/codecov/c/github/ssciwr/mailcom)
![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ssciwr_mailcom&metric=alert_status)
![Language](https://img.shields.io/github/languages/top/ssciwr/mailcom)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ssciwr/mailcom/blob/main/docs/source/notebooks/demo.ipynb)

Tool to parse email body from email text (eml or html file) or csv file, and retain only the text, with names removed. By default for French, Spanish and Portuguese, but can easily be adapted to further languages with the help of configuration files.

## Installation
Create a Python virtual environment, ie. conda. Install `mailcom` into the environment using  
`python -m pip install mailcom`

For an overview over the available languages and models, check the [spaCy](https://spacy.io/usage/models) website. These models are used to sentencize the text, which is important for the subsequent `transformers` pipeline that carries out the Named Entity Recognition (NER).

## How to use mailcom

The package can be configured using the configuration file, for an example see [here](mailcom/default_settings.json). The configuration options are:

| keyword | options [default in parenthesis] | explanation |
| ------- | ------ | ------ |
| `default_lang` | [fr], es, pt | default language of the textual data |
| `pseudo_emailaddresses` | [true], false | replace email addresses by [email] |
| `pseudo_ne` | [true], false | replace named entities by pseudonyms |
| `pseudo_numbers` | [true], false | replace numbers by [number] |
| `ner_pipeline` | [null], [valid transformers model name, revision number, and pipeline, aggregation strategy] | the transformers pipeline to use for the NER | 
| `spacy_model` | ["default"], [valid spaCy model](https://spacy.io/models) | which spaCy model to use for the sentence splitting (see below) |

These keywords set the options for the main processes of the `mailcom` package. The default language can be used for text that is always in the same language, that is, each email/html file or row of the csv contains data in the same language. If this is the case, processing is much faster. If not, the language of the text can be detected on-the-fly with options specified below. In this case, leave the default language empty, ie. `""` an empty string.

The keywords `pseudo_emailaddresses` and `pseudo_numbers` are by default set to `true`, which triggers the replacement of email addresses such as email@gmail.com by [email], and numbers such as 69120 by [number].

By using `pseudo_ne`, the replacement of recognized entities by a pseudonym or spaceholder is triggered. A person's name, i.e. "Michael" is replaced by "James", a location like "Paris" is replaced by [location], an organization such as "GitHub" is replaced by [organization], and other entities like "iPhone 15" are replaced by [misc].

All these three options related to replacement of identifying information can be triggered separately, but are set to `true` by default.

An example for the transformers pipeline is this, with the default options:
```python
"ner": {
    "task": "token-classification",
    "model": "xlm-roberta-large-finetuned-conll03-english",
    "revision": "18f95e9",
    "aggregation_strategy": "simple",
}
```
The task is `token-classification`, which is NER (for a description of the available tasks, see [here]((https://huggingface.co/docs/transformers/en/main_classes/pipelines))). The default model is Hugging Face's default model for this task and default revision number as of January 2025. The aggregation strategy determines how the tokens are aggregated after the pipeline, with `simple` the text is basically reconstructed as it was and the beginning and end of each recognized NER is given in accordance. These options are not likely to be changed, however you may want to use a different model and revision number, which you may change out using the `ner_pipeline` keyword.

The keyword `spacy_model` sets the model to use for the sentencizing. It is important that the initial text is split into sentences as accurate as possible, since this directly affects the subsequent NER accuracy. If the keyword is set to `default`, the models that spaCy uses as default for the given language is used. Some of the default models are:
```
"es": "es_core_news_md"
"fr": "fr_core_news_md"
"de": "de_core_news_md"
"pt": "pt_core_news_md"
```
Other models can directly be passed using this keyword, see the [spaCy reference](https://spacy.io/models). To extend the available languages in `mailcom`, this list needs to be extended. Please also note that not all spaCy models have pipelines with the necessary components.

`mailcom` has additional capabilities that can be used to enhance the text processing:
| keyword | options [default in parenthesis] | explanation |
| ------- | ------ | ------ |
| `lang_detection_lib` | [["langid"]](https://github.com/saffsd/langid.py), ["langdetect"](https://github.com/Mimino666/langdetect), ["trans"](https://huggingface.co/papluca/xlm-roberta-base-language-detection) | automatically detect language of each text using the specified library |
| `lang_pipeline` | [null], {"task": "text-classification"}, [for others see here](https://huggingface.co/docs/transformers/en/main_classes/pipelines) | the pipeline to use for the language detection, only valid for transformers language detection |
| `datetime_detection` | [true], false | detect dates and retain them in the text |
| `time_parsing` | ["non-strict"], "strict" | the pattern matching used to detect date/time patterns in the text (see below) |
| ------- | ------ | ------ |
The first keyword in this table, `lang_detection_lib`, enables dynamic detection of the language. While this increases the processing time, it is crucial for correct sentence splitting when multiple languages are present in the data. In principle, the language can be determined for each sentence; but the general use of this capability is language detection per eml/html file/row in the csv file. Please note that the default language must not be set for this option to be triggered (`default_lang=""`)! Three different libraries are available for language detection, [`langid`](https://github.com/saffsd/langid.py), [`langdetect`](https://github.com/Mimino666/langdetect), [`transformers`](https://huggingface.co/papluca/xlm-roberta-base-language-detection), that all lead to a similar performance on our test set. With the language detected dynamically, the spaCy model for sentence splitting is also set dynamically based on the detected language for each file/row; this should be combined with the `default` option for the spaCy model in order to work correctly.

Using the keyword `datetime_detection`, `mailcom` can detect patterns that match dates, such as "09 février 2009" or "April 17th 2024" for `"non-strict"` parsing. These patterns can then be protected from the replacement of numbers, which would result in (for these examples) "[number] février [number]" or "April [number]th [number]". This feature could be important in texts in which chronology is not easy to follow, or where it is important to retain any information about time in the data.

Setting the `time_parsing` to `"strict"`, only dates such as "17.04.2024" or "17/04/2024" are detected, not using the more advanced pattern matching rules as in "April 17th 2024".

The input data can be provided as eml or html files, or as a csv file. For reading a csv file, more information about the column names needs to be provided. This is explained in the [demo notebook](docs/source/notebooks/demo.ipynb) ([![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ssciwr/mailcom/blob/main/docs/source/notebooks/demo.ipynb)).

First and last names are replaced by pseudonyms. To make the pseudonimized text read more smoothly, names that are common for a specific language can be chosen; but basically any names can be set for any language using the `pseudo_first_names` keyword. The default option is:
```python
pseudo_first_names = {
        "es": [
            "José",
            "Angel",
            "Alex",
            "Ariel",
            "Cruz",
            "Fran",
            "Arlo",
            "Adri",
            "Marce",
            "Mati"
        ],
        "fr": [
            "Claude",
            "Dominique",
            "Claude",
            "Camille",
            "Charlie",
            "Florence",
            "Francis",
            "Maxime",
            "Remy",
            "Cécile"
        ],
        "de": ["Mika"]
    }
```

## Citation
To reference the `mailcom` package in any publication, please use the information provided in the [citation file]().

## Getting in touch
Do not hesitate to open an issue to get in touch with us with requests or questions. Any community contributions are encouraged! Please follow the [contributor's guidelines]().

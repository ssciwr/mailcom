# Evaluation Strategy for `mailcom`

Given the limited availability of free email and text redaction corpora with ground-truth annotations for email addresses, named entities, and numbers, we assessed `mailcom` using both qualitative and quantitative methods for each transformation step. The evaluation strategy is outlined as follows:

## Qualitative Evaluation

For the qualitative evaluation, we focused on the utility and performance of `mailcom` in identifying and pseudonymizing sensitive information on sample data. We also compared `mailcom`'s performance against other open-source pseudonymization tools, including [QualiAnon](https://github.com/pangaea-data-publisher/qualianon), [Amnesia](https://github.com/dTsitsigkos/Amnesia), [Presidio](https://github.com/microsoft/presidio/), and [Scrubadub](https://github.com/LeapBeyond/scrubadub)

### `mailcom` alone

Our sample data was provided by the reasearch group of Sybille Große and the [email donors](https://mailcom.rose.uni-heidelberg.de/), including a set of four short emails in `eml` format and a `csv` file of 103 email contents.  We applied `mailcom` to this sample data and manually reviewed the outputs to assess the effectiveness of the pseudonymization process. The results are summarized as follows:
- **Accuracy**: `mailcom` correctly identified and pseudonymized email addresses, numbers, and most of most of named entities, including people names, organization names, and location names. However, there are some misaligned NER cases, which would be elaborated later.
- **Running Time**: with default settings, we run `mailcom` on an Intel Core Ultra 7 laptop, 32GB RAM (no GPU) and got the following running time (***need to rerun if we use the new version of email detection***):
    - For the 4 `eml` files: around 6.6 seconds
    - For the 103 email contents in the `csv` file: around 10 minutes 20.3 seconds, i.e ~ 6.02 seconds/row

#### Some misaligned cases

In the Frech and Spanish samples among the four short eml files, we observed misalignments in NER results:

* *Location not fully detected*: In the French sample sentence, `"Adresse : 123, rue Principale, 12345 Ville Modèle"`, the default NER model did not recognize `"Principale"` as part of a location entity.
* *Incorrect MISC tagging*: In another French sample sentence,`"April 2024 um 16:53:37 MESZ"`, the substring `"ESZ"` within `"MESZ"` was incorrectly labeled as MISC. This is attributed to a language mismatch, since the default NER model is trained for English while the input sentence is in German.
* *Sentence segmentation issue*: In both the Spanish and French samples, the first sentences were not split as expected. For example, the Spanish text `"El mié., 17 abr. 2024 17:20:18 +0200, Alejandro Rodriguez escribió"` should be treated as a single sentence, but it was incorrectly split into three segments: `"El mié.,"`, `"17 abr."`, and `"2024 17:20:18 +0200, Alejandro Rodriguez escribió"`. 
    * One reason for this is the incorrect sentence splitting by the spaCy models.
    * Another reason is the language mismatch between the used spaCy model and the considered sentences, since some emails have multiple languages. For instance, the French email sample and some French email contents in the `csv` file start with a German sentence.

### `mailcom` vs. other open-source pseudonymization tools

We used the four short sample emails to test similar pseudonymization tools.

#### QualiAnon

Have to install Java17 JDK from amazon, Corretto-17.0.8.8.1 version. **TBU.**

#### Amnesia

Also need to run with Java setup. We tried the [Amnesia playground website](https://amnesia.openaire.eu/demo/mywizard.html) for our sample emails.

Unfortunately, we were unable to use Amnesia for our purpose due to formatting constraints. Specifically, Amnesia requires the input data to be provided as a table with a specific delimiter (e.g. `,`). The tool supports four possible [input table formats](https://www.youtube.com/watch?v=vZbU0n6n01c):
* Simple table: Columns may contain different data types, with each cell holding a single value, e.g. a name or a number
* Table with a set-valued attribute: A fixed number of columns where each column contains a set of values. A delimiter for the set must be specified, e.g. `|`
* Set of values: An arbitrary number of values of the same type.
* Disk-based simple table: Intended for very large datasets, as described in their tutorial video.

None of these options were suitable for our sample data structure, where each email content is a long text containing multiple sentences and is stored in a single cell of a `csv` file.

#### Presidio

We first tried to annonymize the English sample email on the [Presidio demo webpage](https://huggingface.co/spaces/presidio/presidio_demo). None of their provided models were able to cover all name entities and email addresses. For instance:
* Model `spaCy/en_core_web_lg` overlooked organization and event entities, which should be tagged as `ORG` and `MISC`, respectively.
* Model `flair/ner-english-large` missed the event entity.
* Model `HuggingFace/obi/deid_roberta_i2b2` did not recognize the second person entity and misclassified the event entity as organization.
* Model `HuggingFace/StanfordAIMI/stanford-deidentifier-base` mislabeled a normal phrase as an organization and misclassified the event entity as an organization.
* Model `stanza/en` ignored the organization and event entities.

It seems that Presidio by default does not consider arbitrary numbers as sensitive information, which explains why only numbers in date format were detected by some above mentioned models. We therefore discarded the number comparison in our summary above.

We also installed Presidio to use its annonymizer with the same transformer model that we used in our work for NER, i.e. `xlm-roberta-large-finetuned-conll03-english` (see `docs/source/notebooks/test_other_tools.ipynb` notebook). However, the pseudonymized text still could not cover all the expected entities, leaving the second person name and event name (MISC) unmasked.

It is worth noting that under-pseudonymization, especially for person names, can lead to significant privacy risks, while over-pseudonymization can reduce the utility of the data.

#### Scrubadub

By default, Scrubadub only detects email addresses and phone numbers. According to their [documentation](https://scrubadub.readthedocs.io/en/stable/usage.html#adding-an-optional-or-external-detector), user can add custom detectors for address and entity detection. However:
* Adding address detector faced installation issues (Python 3.10 was used)
* Location and event entity were ignored by spaCy entity or name detector

## Quantitative Evaluation

Since there is no available dataset with ground-truth annotations for email addresses, named entities, and numbers, we evaluated each transformation step of `mailcom` separately on relevant benchmark datasets, including email address detection, NER, and number detection. The evaluation scripts are available in the `docs/source/notebooks/quantitative_eval.ipynb` notebook.

Additionally, we compared the results of `mailcom` with `Presidio` for email address detection and NER only, since Presidio and other open-source pseudonymization tools do not explicitly mask all numbers in a text.

In summary, we observed that mailcom yielded comparable results to Presidio for email address detection and outperformed Presidio in NER while using the same transformer model. For number detection, mailcom achieved absolute precision, recall, and F1 score. Below are the detailed evaluation results for each transformation step.

### Email address detection

#### Dataset

We used [Hugging Face `Josephgflowers/PII-NER`](https://huggingface.co/datasets/Josephgflowers/PII-NER) dataset for this evaluation. This dataset is designed for training and evaluating NER models for PII detection. The dataset contains a prompt guiding to extract PII, a multi-paragraph text, and extracted PII entities, such as student name, email address, phone number, driving license, etc. We focused on the email address detection part for our evaluation, hence using only the text and extracted email address entities.

#### Evaluation results

Since we used regular expressions for email address detection, we evaluated the performance of `mailcom` using:

* accuracy: exact match after replacing email addresses by placeholders,
* precision: the proportion of number of detected email addresses that are correct,
* recall: the proportion of actual number of email addresses that are detected,
* F1 score: the harmonic mean of precision and recall.

The evaluation results are as follows:

| Metric    | `mailcom` | `Presidio` |
|-----------|---------|----------|
| Accuracy  | 99.95%    | 99.95%     |
| Precision | 1.0    | 1.0     |
| Recall    | 1.0    | 0.9995     |
| F1 Score  | 1.0    | 0.9998     |

### Name entity detection

For this transformation step, we evaluated on the [Hugging Face `Babelscape/wikineural`](https://huggingface.co/datasets/Babelscape/wikineural) dataset. 

### Number detection

ATIS train dataset
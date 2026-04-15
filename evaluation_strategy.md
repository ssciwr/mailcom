# Evaluation Strategy for `mailcom`

Given the limited availability of free email and text redaction corpora with ground-truth annotations for email addresses, named entities, and numbers, we assessed `mailcom` using both qualitative and quantitative methods for each transformation step. The evaluation strategy is outlined as follows:

## Qualitative Evaluation

For the qualitative evaluation, we focused on the utility and performance of `mailcom` in identifying and pseudonymizing sensitive information on sample data. We also compared `mailcom`'s performance against other open-source pseudonymization tools, including [QualiAnon](https://github.com/pangaea-data-publisher/qualianon), [Amnesia](https://github.com/dTsitsigkos/Amnesia), [Presidio](https://github.com/microsoft/presidio/), and [Scrubadub](https://github.com/LeapBeyond/scrubadub)

### `mailcom` alone

Our sample data was provided by the research group of Sybille Große and the [email donors](https://mailcom.rose.uni-heidelberg.de/), including a set of four short emails in `eml` format and a `csv` file of 103 email contents. We applied `mailcom` to this sample data and manually reviewed the outputs to assess the effectiveness of the pseudonymization process. The results are summarized as follows:
- **Accuracy**: `mailcom` correctly identified and pseudonymized email addresses, numbers, and most of named entities, including people names, organization names, and location names. However, there are some misaligned NER cases, which would be elaborated later.
- **Running Time**: with default settings, we ran `mailcom` on an Intel Core Ultra 7 laptop, 32GB RAM (no GPU), and obtained the following running time (***need to rerun if we use the new version of email detection***):
    - For the 4 `eml` files: around 6.6 seconds
    - For the 103 email contents in the `csv` file: around 10 minutes 20.3 seconds, i.e ~ 6.02 seconds/row

#### Some misaligned cases

In the French and Spanish samples among the four short eml files, we observed misalignments in NER results:

* *Location not fully detected*: In the French sample sentence, `"Adresse : 123, rue Principale, 12345 Ville Modèle"`, the default NER model did not recognize `"Principale"` as part of a location entity.
* *Incorrect MISC tagging*: In another French sample sentence,`"April 2024 um 16:53:37 MESZ"`, the substring `"ESZ"` within `"MESZ"` was incorrectly labeled as MISC. This is attributed to a language mismatch, since the email content is in French while the current sentence is in German.
* *Sentence segmentation issue*: In both the Spanish and French samples, the first sentences were not split as expected. For example, the Spanish text `"El mié., 17 abr. 2024 17:20:18 +0200, Alejandro Rodriguez escribió"` should be treated as a single sentence, but it was incorrectly split into three segments: `"El mié.,"`, `"17 abr."`, and `"2024 17:20:18 +0200, Alejandro Rodriguez escribió"`. 
    * One reason for this is the incorrect sentence splitting by the spaCy models.
    * Another reason is the language mismatch between the used spaCy model and the considered sentences, since some emails have multiple languages. For instance, the French email sample and some French email contents in the `csv` file start with a German sentence.

### `mailcom` vs. other open-source pseudonymization tools

We used the four short sample emails to test similar pseudonymization tools.

#### QualiAnon

Java17 JDK from amazon, Corretto-17.0.8.8.1 version is required to run `QualiAnon`. However, according to their [video tutorial](https://www.youtube.com/watch?v=RYQn4DjdKmo), QualiAnon is not fully automated. The semi-automated part happens where the program replaces masked tokens after user manually defines type and replacement for these tokens. Besides, QualiAnon supports only docx format at the moment and is not designed for large projects (i.e. more than 100 transcripts). It is also unclear if QualiAnon offers general support for different languages. Therefore, we did not further test QualiAnon for our sample data.

#### Amnesia

Amnesia also needs to run with Java setup so we tried the [Amnesia playground website](https://amnesia.openaire.eu/demo/mywizard.html) for our sample emails.

Unfortunately, we were unable to use Amnesia for our purpose due to formatting constraints. Specifically, Amnesia requires the input data to be provided as a table with a specific delimiter (e.g. `,`). The tool supports four possible [input table formats](https://www.youtube.com/watch?v=vZbU0n6n01c):
* Simple table: Columns may contain different data types, with each cell holding a single value, e.g. a name or a number
* Table with a set-valued attribute: A fixed number of columns where each column contains a set of values. A delimiter for the set must be specified, e.g. `|`
* Set of values: An arbitrary number of values of the same type.
* Disk-based simple table: Intended for very large datasets, as described in their tutorial video.

None of these options were suitable for our sample data structure, where each email content is a long text containing multiple sentences and is stored in a single cell of a `csv` file.

#### Presidio

We first tried to anonymize the English sample email on the [Presidio demo webpage](https://huggingface.co/spaces/presidio/presidio_demo). None of their provided models were able to cover all named entities and email addresses. For instance:
* Model `spaCy/en_core_web_lg` overlooked organization and event entities, which should be tagged as `ORG` and `MISC`, respectively.
* Model `flair/ner-english-large` missed the event entity.
* Model `HuggingFace/obi/deid_roberta_i2b2` did not recognize the second person entity and misclassified the event entity as organization.
* Model `HuggingFace/StanfordAIMI/stanford-deidentifier-base` mislabeled a normal phrase as an organization and misclassified the event entity as an organization.
* Model `stanza/en` ignored the organization and event entities.

It seems that Presidio by default does not consider arbitrary numbers as sensitive information, which explains why only numbers in date format were detected by some above mentioned models. We therefore discarded the number comparison in our summary above.

We also installed Presidio to use its anonymizer with the same Transformer model that we used in our work for NER, i.e. `xlm-roberta-large-finetuned-conll03-english` (see `docs/source/notebooks/test_other_tools.ipynb` notebook). However, the pseudonymized text still could not cover all the expected entities, leaving the second person name and event name (MISC) unmasked.

It is worth noting that under-pseudonymization, especially for person names, can lead to significant privacy risks, while over-pseudonymization can reduce the utility of the data.

#### Scrubadub

By default, Scrubadub only detects email addresses and phone numbers. According to their [documentation](https://scrubadub.readthedocs.io/en/stable/usage.html#adding-an-optional-or-external-detector), user can add custom detectors for address and entity detection. However:
* Adding address detector faced installation issues (Python 3.10 was used)
* Location and event entity were ignored by spaCy entity or name detector

## Quantitative Evaluation

Since there is no available dataset with ground-truth annotations for email addresses, named entities, and numbers, we evaluated each transformation step of `mailcom` separately on relevant benchmark datasets, including email address detection, NER, and number detection. The evaluation scripts are available in the `docs/source/notebooks/quantitative_eval.ipynb` notebook.

Additionally, we compared the results of `mailcom` with `Presidio` for email address detection and NER only, since Presidio and other open-source pseudonymization tools do not explicitly mask all numbers in a text.

In summary, we observed that mailcom yielded comparable results to `Presidio` for email address detection and outperformed `Presidio` in NER while using the same Transformer model. For number detection, `mailcom` achieved absolute accuracy, precision, recall, and F1 score. Below are the detailed evaluation results for each transformation step.

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

### Named entity detection

#### Dataset

For this transformation step, we evaluated on the [Hugging Face `Babelscape/wikineural`](https://huggingface.co/datasets/Babelscape/wikineural) dataset. This dataset contains token-level annotations for named entities, including people names, organization names, location names, and miscellaneous entities, specifically:

```
{'O': 0, 'B-PER': 1, 'I-PER': 2, 'B-ORG': 3, 'I-ORG': 4, 'B-LOC': 5, 'I-LOC': 6, 'B-MISC': 7, 'I-MISC': 8}
```

We first extracted the named entities and their types from the dataset, then evaluated the performance of `mailcom` using precision, recall, and F1 score across entity types.

#### Evaluation results

While considering all entity types, `mailcom` achieved the following results:

| Metric    | `mailcom` | `mailcom` on single-sentence input
|-----------|---------|---------|
| Precision | 0.7707    | 0.7743    |
| Recall    | 0.8401    | 0.8431   |
| F1 Score  | 0.8039    | 0.8072   |

Here, the single-sentence input means that we applied `mailcom` on cases where the `spaCy` sentencizer correctly retains the original sentence, which occurs in around 99.4% of the cases in the dataset.

For remaining cases, where the original sentence is split into two or three sentences, the results are lower, as specified in the notebook. This is due to the misalignment between the original sentence and the sentence after splitting, which leads to incorrect index matching for the detected entities. 
* An NER is considered as correct if the detected entity type, text, and start and end indices all match the gold entity. Therefore, even if the detected entity type and text are correct, the misalignment in sentence splitting can cause the start and end indices to be incorrect, resulting in a false negative.
* Some example cases where spaCy sentencizer misaligned the sentences are when the original sentence contains dots in between, such as `No. 1`, `aff.`, `sp.`.

To compare the results with `Presidio` while using the same Transformer model for NER, i.e. `xlm-roberta-large-finetuned-conll03-english`, we only considered the entity types that are commonly detected by both `mailcom` and `Presidio`, which are `PER`, `ORG`, and `LOC`.

| Metric    | `mailcom` | `Presidio` |
|-----------|---------|----------|
| Precision | 0.8825    | 0.6230     |
| Recall    | 0.8760    | 0.4985     |
| F1 Score  | 0.8792    | 0.5538     |

Here, the results of `Presidio` are substantially lower than those of `mailcom`. We did not inspect `Presidio`'s source code and suspect that this discrepancy can be attributed to the default configuration of `Presidio` and the used Transformer model. In [one of the evaluations](https://github.com/microsoft/presidio-research/blob/master/notebooks/5_Evaluate_Custom_Presidio_Analyzer.ipynb) published by `Presidio` on their synthetic datasets, using `StanfordAIMI/stanford-deidentifier-base` model, they achieved around 0.87 precision and 0.84 recall. Therefore, comparing `mailcom` and `Presidio` using other Transformer models for NER, such as `StanfordAIMI/stanford-deidentifier-base`, can be a future direction to further investigate the performance of both tools.

### Number detection

#### Dataset

Since `mailcom` explicitly masks any digits in text, the dataset for this evaluation should fulfill the same requirement. The two datasets used above detect numbers in specific formats, such as license numbers, phone numbers, etc., but not all digits. 

We therefore used ATIS dataset for this purpose. Each token in the dataset is annotated with a slot label, ensuring that all digits are included.

The ATIS train dataset (4978 rows) was used for this evaluation instead of the test dataset (893 rows) to have a larger sample size for evaluation. Since `mailcom`'s number detection does not use any machine learning model, using the train dataset would not cause data leakage issues.

Thanks to [Yun-Nung (Vivian) Chen](https://github.com/yvchen/JointSLU) for publishing this dataset. Download the train dataset [here](https://github.com/yvchen/JointSLU/blob/master/data/atis.train.iob)

#### Evaluation results

| Metric    | `mailcom` |
|-----------|---------|
| Accuracy  | 100%    |
| Precision | 1.0    |
| Recall    | 1.0    |
| F1 Score  | 1.0    |

As `mailcom` explicitly detects any digit character, it achieved absolute accuracy, precision, recall, and F1 score, as expected. We did not compare with `Presidio` for this transformation step since `Presidio` and other open-source pseudonymization tools do not explicitly mask all numbers in a text.

To reproduce the evaluation results, please refer to the `docs/source/notebooks/quantitative_eval.ipynb` notebook.

## Future development

Our future work includes developing a ground-truth annotated dataset and parallelizing the pseudonymization process to further evaluate and improve `mailcom`'s performance.
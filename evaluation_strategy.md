# Evaluation Strategy for `mailcom`

Given the limited availability of free email and text redaction corpora with ground-truth annotations for email addresses, named entities, and numerical data, we assessed mailcom using both qualitative and quantitative methods.

## Qualitative Evaluation

For the qualitative evaluation, we focused on the utility and performance of `mailcom` in identifying and pseudonymizing sensitive information on a sample dataset. We also compared `mailcom`'s performance against other open-source pseudonymization tools, including [QualiAnon](https://github.com/pangaea-data-publisher/qualianon), [Amnesia](https://github.com/dTsitsigkos/Amnesia), [Presidio](https://github.com/microsoft/presidio/), and [Scrubadub](https://github.com/LeapBeyond/scrubadub)

### `mailcom` alone

Our sample data was provided by the reasearch group of Sybille Große and the [email donors](https://mailcom.rose.uni-heidelberg.de/), including a set of four short emails in `eml` format and a `csv` file of 103 email contents.  We applied `mailcom` to this sample data and manually reviewed the outputs to assess the effectiveness of the pseudonymization process. The results are summarized as follows:
- **Accuracy**: `mailcom` correctly identified and pseudonymized email addresses, numerical data, and most of most of named entities, including people names, organization names, and location names. However, there are some misaligned NER cases, which would be elaborated later.
- **Running Time**: with default settings, we run `mailcom` on an Intel Core Ultra 7laptop, 32GB RAM (no GPU) and got the following running time:
    - For the 4 `eml` files: around 6.6 seconds
    - For the 103 email contents in the `csv` file: around 10 minutes 20.3 seconds, i.e ~ 6.02 seconds/row

#### Some misaligned cases

In the Frech and Spanish samples among the four short eml files, we observed misalignments in NER results:

* *Location not fully detected*: In the French sample sentence, `"Adresse : 123, rue Principale, 12345 Ville Modèle"`, the default NER model did not recognize `"Principale"` as part of a location entity.
* *Incorrect MISC tagging*: In another French sample sentence,`"April 2024 um 16:53:37 MESZ"`, the substring `"ESZ"` within `"MESZ"` was incorrectly labeled as MISC. This is attributed to a language mismatch, since the default NER model is trained for English while the input sentence is in German.
* *Sentence segmentation issue*: In both the Spanish and French samples, the first sentences were not split as expected. For example, the Spanish text `"El mié., 17 abr. 2024 17:20:18 +0200, Alejandro Rodriguez escribió"` should be treated as a single sentence, but it was incorrectly split into three segments: `"El mié.,"`, `"17 abr."`, and `"2024 17:20:18 +0200, Alejandro Rodriguez escribió"`. 
    * One reason for this is the incorrect sentence splitting by the spaCy models.
    * Another reason is the language mismatch between the used spaCy model and the considered sentences, since some emails have multiple languages. For instance, the French email sample and some French email contents in the csv file start with a German sentence.

### `mailcom` vs. other open-source pseudonymization tools

We used the four short sample emails to test similar pseudonymization tools.

#### QualiAnon

Have to install Java17 JDK from amazon, Corretto-17.0.8.8.1 version. TBU.

#### Amnesia

Also need to run with Java setup. We tried the [Amnesia playground website](https://amnesia.openaire.eu/demo/mywizard.html) for our sample emails.

Unfortunately, we were unable to use Amnesia for our purpose due to formatting constraints. Specifically, Amnesia requires the input data to be provided as a table with a specific delimiter (e.g. `,`). The tool supports four possible [input table formats](https://www.youtube.com/watch?v=vZbU0n6n01c):
* Simple table: Columns may contain different data types, with each cell holding a single value, e.g. a name or a number
* Table with a set-valued attribute: A fixed number of columns where each column contains a set of values. A delimiter for the set must be specified, e.g. `|`
* Set of values: An arbitrary number of values of the same type.
* Disk-based simple table: ntended for very large datasets, as described in their tutorial video.

None of these options were suitable for our sample data structure, where each email content is a long text containing multiple sentences and is stored in a single cell of a `csv` file.

#### Presidio

#### Scrubadub

## Quantitative Evaluation
from mailcom import utils


class Pseudonymize:
    def __init__(
        self,
        pseudo_first_names: dict,
        trans_loader: utils.TransformerLoader = None,
        spacy_loader: utils.SpacyLoader = None,
    ):

        self.pseudo_first_names = pseudo_first_names

        # records NEs in the last email
        self.ne_list = []

        self.trans_loader = trans_loader
        self.feature = "ner"

        self.spacy_loader = spacy_loader

    def init_spacy(self, language: str, model="default"):
        """Initializes spacy model.

        Args:
            language (str): Language of the desired spacy model.
            model (str, optional): Model specifier. Defaults to "default".
        """
        self.nlp_spacy = utils.get_spacy_instance(self.spacy_loader, language, model)

    def init_transformers(self, pipeline_info: dict = None):
        """Initializes transformers NER model.

        Args:
            pipeline_info (dict, optional): Transformers pipeline info.
        """
        self.ner_recognizer = utils.get_trans_instance(
            self.trans_loader, self.feature, pipeline_info
        )

    def reset(self):
        """Clears the named entity list for processing a new email."""
        # reset NEs
        self.ne_list.clear()

    def get_sentences(self, input_text, language, model="default"):
        """Splits a text into sentences using spacy.

        Args:
            input_text (str): Text to split into sentences.
            language (str): Language for spacy initialization.
            model (str, optional): Model of the spacy instance.
                Defaults to "default".

        Returns:
            list[str]: List of sentences.
        """
        if not hasattr(self, "nlp_spacy"):
            self.init_spacy(language, model)

        doc = self.nlp_spacy(input_text)
        text_as_sents = []
        for sent in doc.sents:
            text_as_sents.append(str(sent))
        return text_as_sents

    def get_ner(self, sentence, pipeline_info: dict = None):
        """Retrieves named entities in a String from transformers model.

        Args:
            sentence (str): Input text to search for named entities.
            pipeline_info (dict, optional): Transformers pipeline info.
                Defaults to None.

        Returns:
            list[dict]: List of named entities retrieved from transformers model.
        """
        if not hasattr(self, "ner_recognizer"):
            self.init_transformers(pipeline_info)
        ner = self.ner_recognizer(sentence)
        return ner

    def choose_per_pseudonym(self, name, lang="fr"):
        """Chooses a pseudonym for a PER named entity based on previously used pseudonyms.
        If the name has previously been replaced, the same pseudonym is used again.
        If not, a new pseudonym is taken from the list of available pseudonyms.

        Args:
            name (str): Word of the named entity.
            lang (str, optional): Language to choose pseudonyms from.
                Defaults to "fr".

        Returns:
            str: Chosen pseudonym.
        """
        pseudonym = ""
        # get list of already replaced names, and list of corresponding pseudonyms
        used_names = [ne["word"] for ne in self.ne_list]
        used_pseudonyms = [
            ne["pseudonym"] if "pseudonym" in ne else "" for ne in self.ne_list
        ]
        # amount of pseudonyms for PER used (PER for "PERSON")
        n_pseudonyms_used = [ne["entity_group"] for ne in self.ne_list].count("PER")
        # check all variations of the name
        name_variations = [
            name,
            name.lower(),
            name.title(),
        ]
        # if this name has been replaced before, choose the same pseudonym
        for nm_var in name_variations:
            pseudonym = (
                used_pseudonyms[used_names.index(nm_var)]
                if nm_var in used_names
                else ""
            )
            if pseudonym != "":
                break
            # if none is found, choose a new pseudonym
            if pseudonym == "":
                try:
                    pseudonym = self.pseudo_first_names[lang][
                        n_pseudonyms_used
                    ]  # reaches end of the list
                except IndexError:
                    pseudonym = self.pseudo_first_names[lang][0]
        return pseudonym

    def pseudonymize_ne(self, ner, sentence, lang="fr"):
        """Pseudonymizes all found named entities in a String.
        Named entities categorized as persons are replaced with a pseudonym.
        Named entities categorized as locations, organizations or miscellaneous
        are replaced by a placeholder. Used pseudonyms are saved for each entity
        for reuse in case of multile occurences.

        Args:
            ner (list[dict]): List of named entities found by the transformers model.
            sentence (str): Input String to replace all named entities in.
            lang (str, optional): Language to choose pseudonyms from.
                Defaults to "fr".

        Returns:
            list[str]: Pseudonymized sentence as list.
        """
        # remove any named entities
        new_sentence = sentence
        # record offset generated by pseudonym lengths different than NE lengths
        offset = 0
        for _, entity in enumerate(ner):
            # process NE
            ent_string = entity["entity_group"]
            ent_word = entity["word"]
            start, end = entity["start"], entity["end"]
            # choose the pseudonym of current NE based on its type
            if ent_string == "PER":
                pseudonym = self.choose_per_pseudonym(ent_word, lang)
            # replace LOC
            elif ent_string == "LOC":
                pseudonym = "[location]"
            # replace ORG
            elif ent_string == "ORG":
                pseudonym = "[organization]"
            # replace MISC
            elif ent_string == "MISC":
                pseudonym = "[misc]"

            # add the pseudonym to the entity dict
            entity["pseudonym"] = pseudonym

            # add this entity to the total NE list
            self.ne_list.append(entity)

            # replace the NE with its pseudonym
            # only replace this occurence of the NE by using start and end positions
            new_sentence = (
                new_sentence[: start + offset]
                + pseudonym
                + new_sentence[end + offset :]  # noqa
            )
            # update offset
            offset += len(pseudonym) - len(ent_word)

        # return new sentence
        newlist = [new_sentence]
        return newlist

    def _get_letter_indices(self, sentence: str, detected_dates: list[str]):
        """Get letter indices of detected dates in the sentence.

        Args:
            sentence (str): Sentence to search for dates.
            detected_dates (list[str]): List of detected dates.

        Returns:
            set: Set of letter indices of detected dates in the sentence.
        """
        if detected_dates is None:
            return set()

        # indices of detected dates
        date_indices = set()
        for date in detected_dates:
            start_pos = 0
            while (start := sentence.find(date, start_pos)) != -1:
                date_indices.update(range(start, start + len(date)))
                start_pos = start_pos + len(date)  # assum no overlapping

        return date_indices

    def pseudonymize_numbers(self, sentence, detected_dates: list[str] = None):
        """Replaces numbers that are not dates in a sentence with placeholder.

        Args:
            sentence (str): Sentence to search for numbers
            detected_dates (list[str], optional): List of detected dates
            which will not be replaced.
                Defaults to None.

        Returns:
            str: Text with non-date numbers replaced by placeholder.
        """
        # indices of detected dates
        date_indices = self._get_letter_indices(sentence, detected_dates)

        sent_as_list = list(sentence)
        new_list = []
        for i in range(len(sent_as_list)):
            potential_num = sent_as_list[i].isdigit() and i not in date_indices
            if potential_num:
                if i == 0 or not sent_as_list[i - 1].isdigit():
                    new_list.append("[number]")
            else:
                new_list.append(sent_as_list[i])

        return "".join(new_list)

    def pseudonymize_email_addresses(self, sentence):
        """Replaces words containing @ in a String with placeholder.

        Args:
            sentence (str): Sentence to search for emails.

        Returns:
            str: Text with emails replaced by placeholder.
        """
        split = sentence.split(" ")
        new_list = []
        for word in split:
            if "@" in word:
                new_list.append("[email]")
            else:
                new_list.append(word)
        return " ".join(new_list)

    def concatenate(self, sentences):
        """Concatenates a list of sentences to a coherent text.

        Args:
            sentences (list[str]): List containing all sentences to concatenate.

        Returns:
            str: Concatenated text.
        """
        return " ".join(sentences)

    def pseudonymize(
        self,
        text,
        language="de",
        model="default",
        pipeline_info: dict = None,
        detected_dates: list[str] = None,
        pseudo_emailaddresses=True,
        pseudo_ne=True,
        pseudo_numbers=True,
    ):
        """Function that handles the pseudonymization of an email
        and all its steps

        Args:
            text (str): Text to pseudonymize.
            language (str, optional): Language of the email. Defaults to "de".
            model (str, optional): Model to use for NER. Defaults to "default".
            pipeline_info (dict, optional): Pipeline information for NER.
                Defaults to None.
            detected_dates (list[str], optional): Detected dates in the email.
                Defaults to None.
            pseudo_emailaddresses (bool, optional): Whether to pseudonymize
                email addresses. Defaults to True.
            pseudo_ne (bool, optional): Whether to pseudonymize named entities.
                Defaults to True.
            pseudo_numbers (bool, optional): Whether to pseudonymize numbers.
                Defaults to True.

        Returns:
            str: Pseudonymized text
        """
        self.reset()
        sentences = self.get_sentences(text, language, model)
        pseudonymized_sentences = []
        for sent in sentences:
            if pseudo_emailaddresses:
                sent = self.pseudonymize_email_addresses(sent)
            if pseudo_ne:
                ner = self.get_ner(sent, pipeline_info)
                sent = (
                    " ".join(self.pseudonymize_ne(ner, sent, language)) if ner else sent
                )
            if pseudo_numbers:
                sent = self.pseudonymize_numbers(sent, detected_dates)
            pseudonymized_sentences.append(sent)
        return self.concatenate(pseudonymized_sentences)

from mailcom import utils
import re
from typing import Optional


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
        self.ne_sent = []  # indices of sentences with NEs
        self.sentences = []  # record sentences obtained by spaCy

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
        self.ne_sent.clear()
        self.sentences.clear()

    def _get_ne_sent_dict(self) -> dict:
        """Convert the list of named entities and their sentence
        indices into a dictionary."""
        ne_sent_dict = {}
        for sent_idx, ne in zip(self.ne_sent, self.ne_list):
            # drop any existing pseudonyms in ne_list
            ne.pop("pseudonym", None)
            if str(sent_idx) not in ne_sent_dict:
                ne_sent_dict[str(sent_idx)] = []
            ne_sent_dict[str(sent_idx)].append(ne)
        return ne_sent_dict

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

        if "sentencizer" not in self.nlp_spacy.pipe_names:
            config = {"punct_chars": [".", "!", "?"]}
            self.nlp_spacy.add_pipe("sentencizer", before="parser", config=config)

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

    def _check_pseudonyms_in_content(self, lang: str = "fr"):
        """Checks if any of the pseudonyms are present in the current content.

        Args:
            lang (str): Language context of the data, defaults to "fr".
        """
        names = []
        exclude_pseudonym = False

        # also take into account that the language may not have defined pseudos
        # in this case, take the first available language
        if lang not in self.pseudo_first_names:
            lang = next(iter(self.pseudo_first_names))

        for entity in self.ne_list:
            if entity["entity_group"] == "PER":
                name = entity["word"]
                # here we should consider first names only, without
                # the given name after the space
                name = name.split(" ")[0] if " " in name else name
                (
                    names.extend([name, name.lower(), name.title()])
                    if name not in names
                    else None
                )
        # now we have collected all possible names, lets check for a match
        if any(pseudo in names for pseudo in self.pseudo_first_names.get(lang, [])):
            print("Found matching name(s) from pseudonyms to actual person names.")
            print(f"Names found: {names}")
            print(f"Pseudonyms provided: {self.pseudo_first_names.get(lang, [])}")
            exclude_pseudonym = True
            # drop the pseudonym from all further processing
            self.pseudo_first_names[lang] = [
                pseudo
                for pseudo in self.pseudo_first_names[lang]
                if pseudo not in names
            ]
            print(f"Updated pseudonyms: {self.pseudo_first_names.get(lang, [])}")
        # raise an exception for the user to restart with other pseudonyms if there are
        # no pseudonyms left in the list
        if not self.pseudo_first_names.get(lang, []):
            raise ValueError(
                """Please provide a different list of pseudonyms via the
                             workflow settings file. The current list of pseudonyms
                             is empty or too short and contains only names that already
                             exist in the actual data."""
            )
        return exclude_pseudonym

    def choose_per_pseudonym(self, name, lang="fr", prev_ne_list: list = None):
        """Chooses a pseudonym for a PER named entity based on previously used pseudonyms.
        If the name has previously been replaced, the same pseudonym is used again.
        If not, a new pseudonym is taken from the list of available pseudonyms.

        Args:
            name (str): Word of the named entity.
            lang (str, optional): Language to choose pseudonyms from.
                Defaults to "fr".
            prev_ne_list (list, optional): List of named entities from previous fields
                in the email.
                Defaults to None.

        Returns:
            str: Chosen pseudonym.
        """

        def _get_used_names(ne_list):
            return [ne["word"] for ne in ne_list] if ne_list else []

        def _get_used_pseudonyms(ne_list):
            return [ne.get("pseudonym", "") for ne in ne_list] if ne_list else []

        def _get_n_pseudonyms_used(ne_list):
            return [ne["entity_group"] for ne in ne_list].count("PER") if ne_list else 0

        if lang not in self.pseudo_first_names:
            # get name from the first specified language
            lang = next(iter(self.pseudo_first_names))

        pseudonym = ""
        # get list of already replaced names, and list of corresponding pseudonyms
        used_names = _get_used_names(self.ne_list) + _get_used_names(prev_ne_list)
        used_pseudonyms = _get_used_pseudonyms(self.ne_list) + _get_used_pseudonyms(
            prev_ne_list
        )
        # amount of pseudonyms for PER used (PER for "PERSON")
        n_pseudonyms_used = _get_n_pseudonyms_used(
            self.ne_list
        )  # count only actually used pseudonyms, i.e. not count prev_ne_list
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

    def pseudonymize_ne(
        self, ner, sentence, lang="fr", sent_idx=0, prev_ne_list: list = None
    ):
        """Pseudonymizes all found named entities in a String.
        Named entities categorized as persons are replaced with a pseudonym.
        Named entities categorized as locations, organizations or miscellaneous
        are replaced by a placeholder. Used pseudonyms are saved for each entity
        for reuse in case of multiple occurrences.

        Args:
            ner (list[dict]): List of named entities found by the transformers model.
            sentence (str): Input String to replace all named entities in.
            lang (str, optional): Language to choose pseudonyms from.
                Defaults to "fr".
            sent_idx (int, optional): Index of the sentence in the email.
                Defaults to 0.
            prev_ne_list (list, optional): List of named entities from previous
                fields in the email. Defaults to None.

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
                pseudonym = self.choose_per_pseudonym(
                    ent_word, lang, prev_ne_list=prev_ne_list
                )
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
            self.ne_sent.append(sent_idx)

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
        split = re.split(r"\s+", sentence)  # split by any whitespace
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
        language="fr",
        model="default",
        pipeline_info: dict = None,
        detected_dates: list[str] = None,
        pseudo_emailaddresses=True,
        pseudo_ne=True,
        pseudo_numbers=True,
        prev_ne_list: list = None,
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
            prev_ne_list (list, optional): List of named entities from previous
                fields in the email. Defaults to None.

        Returns:
            str: Pseudonymized text
        """
        self.reset()
        self.sentences = self.get_sentences(text, language, model)
        pseudonymized_sentences = []
        for sent_idx, sent in enumerate(self.sentences):
            if pseudo_emailaddresses:
                sent = self.pseudonymize_email_addresses(sent)
            if pseudo_ne:
                ner = self.get_ner(sent, pipeline_info)
                sent = (
                    " ".join(
                        self.pseudonymize_ne(
                            ner, sent, language, sent_idx, prev_ne_list=prev_ne_list
                        )
                    )
                    if ner
                    else sent
                )
            if pseudo_numbers:
                sent = self.pseudonymize_numbers(sent, detected_dates)
            pseudonymized_sentences.append(sent)
        # check that pseudonyms are not the same as actual
        # names in the current content
        # if they are, the pseudonym is dropped for the present and all future content
        exclude_pseudonym = (
            self._check_pseudonyms_in_content(lang=language) if self.ne_list else False
        )
        return self.concatenate(pseudonymized_sentences), exclude_pseudonym

    def pseudonymize_with_updated_ne(
        self,
        sentences,
        ne_sent_dict: Optional[dict[list[dict]]],
        language="fr",
        detected_dates: list[str] = None,
        pseudo_emailaddresses=True,
        pseudo_ne=True,
        pseudo_numbers=True,
        prev_ne_list: list = None,
    ):
        """Pseudonymizes the email with updated named entities.
        This function is used when the named entities have been updated
        in the email and need to be pseudonymized again.

        Args:
            sentences (list[str]): List of sentences to pseudonymize.
            ne_sent_dict (dict[list[dict]]|None): Dictionary containing named entities.
                If set to none, the previous named entities will be used. This is the case
                for reprocessing emails with new pseudonyms.
            language (str, optional): Language of the email. Defaults to "de".
            detected_dates (list[str], optional): Detected dates in the email.
                Defaults to None.
            pseudo_emailaddresses (bool, optional): Whether to pseudonymize
                email addresses. Defaults to True.
            pseudo_ne (bool, optional): Whether to pseudonymize named entities.
                Defaults to True.
            pseudo_numbers (bool, optional): Whether to pseudonymize numbers.
                Defaults to True.
            prev_ne_list (list, optional): List of named entities from previous
                fields in the email. Defaults to None.

        Returns:
            str: Pseudonymized text
        """
        if not ne_sent_dict:
            # the ne was ok last time, but we need to rerun with new pseudonyms
            ne_sent_dict = self._get_ne_sent_dict()

        self.reset()
        self.sentences = sentences
        pseudonymized_sentences = []
        for sent_idx, sent in enumerate(sentences):
            if pseudo_emailaddresses:
                sent = self.pseudonymize_email_addresses(sent)
            if pseudo_ne:
                sent = (
                    " ".join(
                        self.pseudonymize_ne(
                            ne_sent_dict[str(sent_idx)],
                            sent,
                            language,
                            sent_idx,
                            prev_ne_list=prev_ne_list,
                        )
                    )
                    if str(sent_idx) in ne_sent_dict
                    else sent
                )
            if pseudo_numbers:
                sent = self.pseudonymize_numbers(sent, detected_dates)
            pseudonymized_sentences.append(sent)
        # check that pseudonyms are not the same as actual
        # names in the current content
        # if they are, the pseudonym is dropped for the present and all future content
        exclude_pseudonym = (
            self._check_pseudonyms_in_content(lang=language) if self.ne_list else False
        )
        return self.concatenate(pseudonymized_sentences), exclude_pseudonym

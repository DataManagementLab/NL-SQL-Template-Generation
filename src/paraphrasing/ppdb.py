# coding=utf-8
""" ppdb paraphraser class
"""
import json
import logging
import random
from copy import copy


# TODO other paraphrasing methods
# TODO intelligent selection for training data (crowd sourcing? quality heuristic?)


class PPDB:
    """
    Paraphraser based on PPDB

    implements paraphrasing through replacement of tokens with PPDB provided paraphrases
    and through random token deletion

    Attributes:
        int rand_drop_scale: random word drop scale
        float rand_drop_p: random drop probability per token
        int scale: paraphrasing scale
        dict paraphrases: paraphrasing dictionary
        dict position: for previously paraphrased tokens saves the index of the next paraphrase

    """

    def __init__(self, filename, scale, rand_drop_scale, rand_drop_p):
        """
        create PPDB paraphraser object

        :param str filename: path to PPDB file
        :param int scale: paraphrasing scale
        :param int rand_drop_scale: random word drop scale
        :param float rand_drop_p: random drop probability
        """

        self.rand_drop_scale = rand_drop_scale
        self.rand_drop_p = rand_drop_p
        self.scale = scale

        self.paraphrases = {}
        self.position = {}

        if self.scale > 0:  # No need if pp_scale is 0 = paraphrasing disabled
            with open(filename) as open_file:
                self.paraphrases = json.load(open_file)

            logging.info('PPDB paraphrases loaded!')
        else:
            logging.info('Paraphrasing disabled')

    def get_candidate_count(self, tokens):
        """
        determines the number of tokens that could be paraphrased with the dictionary

        :param list tokens: list of tokens of a NL query
        :return int: number of tokens in the list available in the paraphrasing dictionary
        """

        count = 0
        for t in tokens:
            if t in self.paraphrases:
                count += 1

        return count

    def get_substitution_paraphrase(self, tokens):
        """
        generate paraphrase by randomly substituting one token with one of its paraphrases

        :param list tokens: list of tokens of a NL query
        :return list: list of tokens of a paraphrase of the NL query
        """

        num_candidates = self.get_candidate_count(tokens)

        if not num_candidates:
            return None

        random_index = random.randint(0, num_candidates - 1)
        paraphrasable_index = -1

        for i in range(0, len(tokens)):
            if tokens[i] in self.paraphrases:

                paraphrasable_index += 1

                # use all available paraphrases for a token before reusing
                if paraphrasable_index == random_index:

                    # token chosen for the first time
                    if not tokens[i] in self.position:
                        random.shuffle(self.paraphrases[tokens[i]])
                        self.position[tokens[i]] = 0

                    old_position = self.position[tokens[i]]
                    self.position[tokens[i]] = (self.position[tokens[i]] + 1) % len(self.paraphrases[tokens[i]])
                    tokens[i] = self.paraphrases[tokens[i]][old_position]  # actual paraphrasing

                    break

        return tokens

    def get_paraphrases(self, tokens):
        """
        generate paraphrases for a NL token list

        :param list tokens: list of tokens of a NL query
        :return:
        """

        # trivial paraphrase; original phrase
        paraphrase_tokens = [tokens]

        # generate paraphrases by substituting with paraphrasing dictionary
        for i in range(0, self.scale):
            paraphrase = self.get_substitution_paraphrase(copy(tokens))
            if paraphrase:
                paraphrase_tokens.append(paraphrase)

        # generate paraphrases by randomly dropping tokens
        # TODO individual drop probabilities for tokens?
        paraphrases = []
        for original in paraphrase_tokens:
            paraphrases.append(' '.join(original))
            if self.rand_drop_scale:
                for to_remove in random.sample(original, min(self.rand_drop_scale, len(original))):
                    if random.random() > self.rand_drop_p:
                        continue

                    paraphrase = copy(original)
                    paraphrase.remove(to_remove)

                    paraphrases.append(' '.join(paraphrase))

        return paraphrases

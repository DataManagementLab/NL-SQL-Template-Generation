# coding=utf-8
import argparse
import json

import requests
from nltk.translate.bleu_score import sentence_bleu

# TODO
URL = ''
API_KEY = ''


# Please note that there is no input checking for language codes.
# Full list of supported languages can be found at https://cloud.google.com/translate/docs/languages

class PivotParaphraser:
    def __init__(self):
        pass

    def executeRequest(self, query, language):
        params = {'q': query, 'target': language, 'key': API_KEY}
        r = requests.post(url=URL, data=params)
        return r.text

    def singleTranslation(self, query, languages, file):
        cur_query = query
        for lang in languages:
            response = self.executeRequest(cur_query, lang)
            json_response = json.loads(response)
            cur_query = json_response['data']['translations'][0]['translatedText']
        if (file == ''):
            print(cur_query)
        else:
            formatted = 'u\'' + cur_query + '\''
            formatted = cur_query.encode('utf8')
            newlineFormat = '\n'.encode('utf8')
            file.write(formatted + newlineFormat)
            return cur_query

    def fileTranslation(self, inFile, outFile, languages):
        inF = open(inFile, "r")
        if (inF.mode == 'r'):
            lines = inF.readlines()

            # no error checking for out file
            # count = 0
            total_lines = 0
            outF = open(outFile, "wb+") if outFile != '' else ''
            for line in lines:
                total_lines += 1
                returned = self.singleTranslation(line, languages, outF)
                # if (line == returned):
                #     count += 1
                score = sentence_bleu([line.split(' ')], returned.split(' '))
                print(score)
            # print(count / total_lines)
            print(total_lines)
        else:
            print('cannot open inFile')
            exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pivot paraphraser')
    parser.add_argument('--query', action='store', dest='query', default='',
                        help='single query translation, enclose with quotes. use this OR --inFile')
    parser.add_argument('--lang', action='store', dest='lang', default='en',
                        help='languages to translate, separated with |, encased in quotes . last language is output language')
    parser.add_argument('--inFile', action='store', dest='inFile', default='',
                        help='read in list of queries to translate. use this OR --query')
    parser.add_argument('--outFile', action='store', dest='outFile', default='',
                        help='write output to file, only to be used with --inFile')

    args = parser.parse_args()

    query = args.query
    inFile = args.inFile
    outFile = args.outFile
    lang = args.lang

    # input checking
    if (query == '' and inFile == ''):
        print('no input specified')
        exit(1)

    if (query != '' and inFile != ''):
        print('can only specify query or file, not both')
        exit(1)

    lang_list = lang.split('|')
    p = PivotParaphraser()
    if (query != ''):  # single translation
        p.singleTranslation(query, lang_list, '')
    else:  # file translation
        p.fileTranslation(inFile, outFile, lang_list)


import argparse
import collections
import spacy


class CorpusStats:

    def __init__(self, corp):
        self.__corpus = corp
        self.__stats = {}
        self.__spacy = spacy.load('xx_ent_wiki_sm')
        self.compute()

    def compute(self):
        docs = self.__corpus.getDocument()

        self.__stats['Total'] = {}
        self.__stats['Total']['All'] = self.subsetStats()
        self.__stats['By gender'] = self.breakdown(docs, 'gender')
        self.__stats['By region'] = self.breakdown(docs, 'region')
        self.__stats['By native'] = self.breakdown(docs, 'is_native')
        self.__stats['By ocupation'] = self.breakdown(docs, 'occupation')
        self.__stats['By submission type'] = self.breakdown(docs, 'submission_type')
        self.__stats['By translation lang'] = self.breakdown(docs, 'source_language')
        self.__stats['Number of errors'] = self.countErrors(docs)

    def subsetStats(self, docs):
        stats = {}
        stats['Documents'] = len(docs)
        stats['Sentences'] = sum(self.countSentences(doc.source) for doc in docs)
        stats['Tokens'] = sum(self.countTockens(doc.source) for doc in docs)
        stats['Unique users'] = len(set(doc.meta.authorId) for doc in docs)

        return stats

    def resetStats(self):
        pass

    def prettyPrint(self):
        for i, j in sorted(self.__stats.items()):
            print(f'# {i}')
            for key, val in j.items():
                print(f'{key:<30} {val}')
            print()

    def countSentences(self, sentence):
        for _ in range(20):
            sentence = sentence.replace('..', '.')

        return sentence.count('.') + sentence.count('?') + sentence.count('!')

    def countTokens(self, sentence):
        tokens = self.__spacy(sentence, disable=['parser', 'ner'])
        return len(tokens)

    def _count_errors(self, docs):
        errors = collections.Counter()

        for i in docs:
            for j in i.annotated.getAnnotations():
                try:
                    errors[j.meta['error_type']] += 1
                except KeyError:
                    print(i.docId)
                    print(j)
                    raise
                    continue

                errors['TOTAL'] += 1
        return errors


def main(args):
    from corpus import Corpus

    corp = Corpus(args.partition)
    stats = CorpusStats(corp)
    stats.prettyPrint()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('partition', choice=['all', 'train', 'test'])
    args = parser.parse_args()
    main(args)






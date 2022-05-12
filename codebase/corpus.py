
import csv
import collections
import pathlib

from annotated_text import AnnotatedTxt

Metadata = collections.namedtuple("Metadata",
    "doc_id author_id is_native region gender occupation submission_type "
    "source_language annotator_id partition is_sensitive")


class Document:

    def __init__(self, annotated, meta):
        self.__annotated = annotated
        self.__meta = meta

    def __str__(self):
        return self.annotated

    def __repr__(self):
        return f'<Document {self.annotated}>'

    @property
    def annotated(self):
        return self.__annotated

    @property
    def source(self):
        return self.annotated.getOriginalText()

    @property
    def target(self):
        return self.annotated.getCorrectedText()

    @property
    def docId(self):
        return self.__meta.docId


class Corpus:

    def __init__(self, partition='train'):
        if partition not in ('train', 'test', 'all'):
            raise ValueError('partition must be train, test, or all.')

        self.__partition = partition
        self.__annotatorId = '1'

        rootDir = pathlib.Path(__file__).parent
        self.__dataDir = rootDir/'data'
        self.__metaData = None
        self.__doc = None

    def __repr__(self):
        return f'<Corpus(partition={self.__partition}, len={len(self)} docs>'

    def __str__(self):
        return repr(self)

    def __iter__(self):
        return self.__iterDocuments

    def __len__(self):
        return len(self.getMetadata())

    def getMetadata(self):
        if self.__metaData is None:
            self.loadMetadata()

        return self.__metaData

    def loadMetadata(self):
        self.__metaData = []
        reader = csv.DictReader((self.__dataDir/'metadata.csv').open())

        for row in reader:
            if self.__partition == 'all' or row['partition'] == self.__partition:
                record = Metadata(
                    doc_id=row['id'], author_id=row['author_id'], is_native=row['is_native'],
                    region=row['region'], gender=row['gender'], occupation=row['occupation'],
                    submission_type=row['submission_type'], source_language=row['source_language'],
                    annotator_id=int(row['annotator_id']), partition=row['partition'],
                    is_sensitive=bool(int(row['is_sensitive']))
                )
                self.__metaData.append(record)

    def iterDocuments(self):
        if self.__doc is not None:
            return iter(self.__doc)

        for meta in self.getMetadata():
            fn = f'{meta.docId}.a{self.__annotatorId}.ann'
            path = self.__dataDir/meta.partition/'annotated'/fn
            text = AnnotatedTxt(path.read_text())
            document = Document(text, meta=meta)
            yield document

    def getDocument(self):
        if self.__doc is None:
            self.__doc = list(self.iterDocuments())

        return self.__doc

    def getDoc(self, docId):
        document = self.getDocument()
        result = [i for i in document if i.docId == docId]

        if not result:
            raise LookupError(f'Document {docId} is not found')

        assert len(result) == 1
        return result[0]
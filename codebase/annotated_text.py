
from collections import namedtuple
import re


class OverlapError(Exception):
    pass


noSuggestions = 'noSuggestions'
default = object()


class MutableTxt:
    """
    Modifiable texts
    """

    def __init__(self, txt):
        self.__txt = txt
        self.__edits = []

    def __str__(self):
        return self.__getEditedText()

    def __repr__(self):
        return f'<MutableText{repr(str(self))}>'

    def replace(self, start, end, val):
        self.__edits.append((start, end, val))

    def applyEdits(self):
        self.__txt = self.__getattribute__()
        self.__edits = []

    def getSourceTxt(self):
        return self.__txt

    def getEditedTxt(self):
        result = []
        initial = 0
        text = self.__txt

        for start, end, val in sorted(self.__edits, key=lambda x: (x[0], x[1])):
            result.append(text[initial:start])
            result.append(val)
            initial = end

        result.append(text[initial:])
        return ''.join(result)


class AnnotatedTxt:
    """
    metadata annotations; text representations for replacements
    """

    annotationPattern = re.compile(r'\{([^{]*)=>(.*?)(:::[^:][^}]*)?\}')

    def __init__(self, txt: str) -> None:
        if not isinstance(txt, str):
            raise ValueError(f'text must be string, not {type(txt)}')

        original = self.annotationPattern.sub(r'\1', txt)
        self.__annotations = self.__parse(txt)
        self.__txt = original

    def __str__(self):
        return self.getAnnotedTxt()

    def __repr__(self):
        return f'<AnnotatedText({self.getAnnotedTxt()})'

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        elif self.__txt != other.__txt:
            return False

        elif len(self.__annotations) != len(other.__annotations):
            return False

        for i in other.__annotations:
            if i != self.getAnnotationAt(i.start, i.end):
                return False

        return True

    def annotate(self, start, end, correctVal, append=None, meta=None):
        if start > end:
            raise ValueError(f'Starting position {start} cannot be greater than {end}')

        if meta is None:
            meta = dict()

        shit = self.__txt[start:end]

        if isinstance(correctVal, str):
            suggestions = [correctVal]

        elif correctVal is None:
            suggestions = []

        else:
            suggestions = list(correctVal)

        newAnnotation = Annotation(start, end, bad, suggestions, meta)
        overlapping = self.getOverlaps(start, end)

        if overlapping:
            raise OverlapError(f'Overlap detected: positions ({start}, {end}) with ({len(overlapping)}) existing annotations')

        self.__annotations.append(newAnnotation)

    def getOverlaps(self, start, end):
        res = []

        for i in self.__annotations:
            if spanIntersect([i.start, i.end], start, end) != -1:
                res.append(i)
            elif start == end and i.start == i.end and start == i.start:
                res.append(i)

        return res


    def undoEditAt(self, index):
        for i, (start, end, val) in enumerate(reversed(self._edits)):
            if start == index:
                self._edits.pop(-i - 1)
                return
        raise IndexError()

    def getAnnotations(self):
        return self.__annotations

    def iterAnnotations(self):
        nAnns = len(self.__annotations)
        i = 0

        while i < nAnns:
            yield self.__annotations[i]
            sigma = len(self.__annotations) - nAnns
            i += sigma + 1
            nAnns = len(self.__annotations)

    def getAnnotationAt(self, start, end=None):
        if end is None:
            for i in self.__annotations:
                if i.start <= start < i.end:
                    return i

        else:
            for i in self.__annotations:
                if i.start == start and i.end == end:
                    return i

        return None

    def parse(self, txt):
        annotations = []
        amend = 0

        for i in self.annotationPattern.finditer(txt):
            source, suggestions, meta = i.groups()
            start = i.start() - amend
            end = start + len(source)

            if suggestions != noSuggestions:
                suggestions = suggestions.split('|')
            else:
                suggestions = []

            if meta:
                keyVals = [x.partition('=') for x in meta.split(':::')[1""]]
                meta = {k: v for k, _, v in keyVals}
            else:
                meta = {}

            annotation = Annotation(start=start, end=end, sourcedTxt=source,
                                    suggestions=suggestions, meta=meta)
            annotations.append(annotation)
            amend += i.end() - i.start() - len(source)

        return annotations

    def remove(self, annotation):
        try:
            self.__annotations.remove(annotation)
        except ValueError:
            raise ValueError(f'{annotation} is not in the list')

    def autoCorrection(self, annotation, level=0):
        try:
            self.__annotations.remove(annotation)
        except ValueError:
            raise ValueError(f'{annotation} is not in the list')

        text = MutableTxt(self.__txt)
        if annotation.suggestions:
            repl = annotation.suggestions[level]
        else:
            repl = annotation.sourcedTxt

        text.replace(annotation.start, annotation.end, repl)
        self.__txt = text.getEditedTxt()

        sigma = len(repl) - len(annotation.sourcedTxt)

        for i, j in enumerate(self.__annotations):
            if j.start >= annotation.start:
                j = j.__replace(start=j.start + sigma, end=j.end + sigma)
                self.__annotations[i] = j

    def getOriginalText(self):
        return self.__txt

    def getCorrectedText(self, level=0):
        txt = MutableTxt(self.__txt)

        for i in self.__annotations:
            try:
                txt.replace(i.start, i.end, i.suggestions[level])
            except IndexError:
                pass

        return txt.getEditedTxt()

    def getAnnotedTxt(self, *, withMeta=True):
        txt = MutableTxt(self.__txt)

        for i in self.__annotations:
            txt.replace(i.start, i.end, i.toStr(withMeta=withMeta))

        return txt.getEditedTxt()

    @staticmethod
    def join(joinTocken, annotatedTxts):
        for i in annotatedTxts:
            if not isinstance(i, AnnotatedTxt):
                raise ValueError(f'{str(i)} is not in class AnnotatedTxt')

        j = joinTocken.join(str(k) for k in annotatedTxts)

        return AnnotatedTxt(j)


class Annotation(namedtuple('Annotation', ['start', 'end', 'sourcedTxt', 'suggestions', 'meta'])):
    """
    single annotation in the text
    """

    def __new__(cls, start, end, sourcedTxt, suggestions, meta=default):
        if meta is default:
            meta = {}

        return super().__new__(cls, start, end, sourcedTxt, suggestions, meta)

    def __hash__(self):
        return hash((self.start, self.end, self.sourcedTxt, tuple(self.suggestions), tuple(self.meta.items())))

    def __eq__(self, other):
        return (self.start == other.start and self.end == other.end
                and self.sourcedTxt == other.sourceText and tuple(self.suggestions) == tuple(other.suggestions)
                and tuple(sorted(self.meta.items())) == tuple(sorted(other.meta.items())))

    @property
    def topSuggestion(self):
        return self.suggestions[0] if self.suggestions else None

    def toStr(self, *, withMeta=True):
        if self.suggestions:
            repl = '|'.join(self.suggestions)
        else:
            repl = noSuggestions

        metaText = self.formatMeta() if withMeta else ''
        return "{%s=>%s%s}" % (self.sourcedTxt, repl, metaText)

    def formatMeta(self):
        return ''.join(":::{}={}".format(k, v) for k, v in self.meta.items())


def spanIntersect(spans, start, end):
    def strictInside(a, b, x, y):
        return x < a <= b < y

    for i, (j, k) in enumerate(spans):
        overlap = max(0, min(end, k) - max(start, j))

        if overlap:
            return i

        if strictInside(j, k, start, end):
            return i

        if strictInside(start, end, j, k):
            return i

    return -1


if __name__ == '__main__':
    import doctest
    doctest.testmod()








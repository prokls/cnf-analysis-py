#!/usr/bin/env python3

"""
    cnfanalysis.statsfile
    ---------------------

    *statsfile* library to process ``.stats`` files.

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import json

import xml.dom.minidom
import xml.etree.ElementTree

import xml.sax.saxutils
import xml.sax.handler


class Writer:
    """Write metric to a file descriptor"""

    def __init__(self, fd, format='json', encoding='utf-8'):
        self.writer = self.writer.__enter__()
        if format.lower() == 'xml':
            self.writer = IncrementalXmlWriter(fd, encoding=encoding)
        else:
            self.writer = IncrementalJsonWriter(fd, encoding=encoding)

    def start_metric(self):
        self.cache = { 'metric': {} }

    def receive(self, key, value):
        if key.startswith('@'):
            self.cache[key[1:]] = value
        else:
            self.cache['metric'][key] = value

    def end_metric(self):
        self.writer.write(self.cache)

    def finish(self):
        self.writer.__exit__(None, None, None)


class IncrementalXmlWriter(xml.sax.handler.ContentHandler):
    """Write an XML incrementally. Uses the basic idea of SAX XML APIs,
    but specifically writes down metrics.

    Example::

        >>> with open('test.xml', 'wb') as fd:
        ...     with IncrementalXmlWriter(fd, encoding='utf-8') as writer:
        ...         writer.write(data)
    """

    def __init__(self, filedescriptor, *, encoding='utf-8'):
        self.root = 'metrics'
        self.gen = xml.sax.saxutils.XMLGenerator(filedescriptor,
            encoding=encoding, short_empty_elements=True)

    def __enter__(self):
        self.gen.startDocument()
        self.gen.startElement(self.root, {})
        self.gen.ignorableWhitespace("\n  ")
        return self

    def write(self, metric):
        """Write a metric to the XML file"""
        # attributes
        attributes = {}
        for key, value in metric.items():
            if key == 'metric':
                continue
            if isinstance(value, str):
                attributes[key] = value
            else:
                attributes[key] = ','.join(value)

        self.gen.startElement('file', attributes)
        self.gen.ignorableWhitespace("\n    ")

        del attributes

        count = len(metric['metric'])
        for key, value in metric['metric'].items():
            self.gen.startElement('metric', {key: str(value)})
            self.gen.endElement('metric')

            if count != 1:
                self.gen.ignorableWhitespace("\n    ")
            else:
                self.gen.ignorableWhitespace("\n  ")
            count -= 1

        self.gen.endElement('file')
        self.gen.ignorableWhitespace("\n")

    def __exit__(self, type, value, traceback):
        self.gen.endElement(self.root)
        self.gen.ignorableWhitespace("\n")
        self.gen.endDocument()


class IncrementalJsonWriter:
    """Write a JSON incrementally. Applies the idea of SAX XML APIs to JSON
    to specifically writes down metrics.

    Example::

        >>> with open('test.json', 'wb') as fd:
        >>>     with IncrementalJsonWriter(fd, encoding='utf-8') as writer:
        >>>         writer.write(data)
    """

    def __init__(self, filedescriptor, *, encoding='utf-8'):
        self.fd = filedescriptor
        self.enc = encoding
        self.first = True

    def __enter__(self):
        self.fd.write('{\n  "metrics": [\n    '.encode(self.enc))
        return self

    def write(self, metric):
        """Write a metric to the JSON file"""
        if not self.first:
            self.fd.write(',\n    '.encode(self.enc))
        else:
            self.first = False

        obj = json.dumps(metric, indent=2, sort_keys=True).replace('\n', '\n    ')
        self.fd.write(obj.encode(self.enc))

    def __exit__(self, type, value, traceback):
        self.fd.write('\n  ]\n}\n'.encode(self.enc))


class YieldingXmlReader(xml.sax.handler.ContentHandler):
    """Read a stats XML file and yield all metrics to a generator.

    Example::

        >>> def r():
        ...     while True:
        ...         val = yield
        ...         print(val)
        ... 
        >>> with YieldingXmlReader(r()) as reader:
        ...     xml.sax.parse('test.xml', reader)
    """

    def __init__(self, generator):
        self.gen = generator
        self.metrics = {}

    def __enter__(self):
        return self

    def read(self):
        next(self.gen)
        self.gen.send(self.metrics)

    def __exit__(self, type, value, traceback):
        self.gen.close()

    def startElement(self, name, attrs):
        if name == 'file':
            self.metrics.update(attrs)
            self.metrics['metric'] = {}
        elif name == 'metric':
            for key, val in attrs.items():
                self.metrics['metric'][key] = val

    def endElement(self, name):
        if name == 'file':
            self.read()
            self.metrics = {}


class IteratingJsonReader:
    """Parse a JSON file and provide an iterator to iterate over metrics.
    Example::

        >>> with open('test.json', 'r', encoding="utf-8") as fd:
        >>>     with IteratingJsonReader(fd) as reader:
        >>>         for obj in reader:
        >>>             print(obj)
    """

    def __init__(self, filedescriptor):
        self.fd = filedescriptor

    def __enter__(self):
        self.metrics = json.load(self.fd, parse_float=float, parse_int=int)
        self.i = 0
        return self

    def __exit__(self, type, value, traceback):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        if self.i == len(self.metrics['metrics']):
            raise StopIteration()

        metric = self.metrics['metrics'][self.i]
        self.i += 1
        return metric

#!/usr/bin/env python3

"""
    cnfanalysis.statsfile
    ---------------------

    *statsfile* library to process ``.stats`` files
    generated from CNF files.

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import json

import xml.dom.minidom
import xml.etree.ElementTree

import xml.sax.saxutils
import xml.sax.handler



def detect_format(filepath):
    """Given a statsfile of unknown format.
    Detect the format by reading the first byte.

    Feature: File descriptors as argument should also work

    :param filepath:        Read one byte from this filepath to detect format
    :type filepath:         str
    :return:                'xml' or 'json'
    :rtype:                 str
    """
    try:
        with open(filepath, 'r') as fp:
            by = fp.read(1)
    except TypeError:
        # assume filepath is file descriptor
        by = fp.read(1)
        fp.seek(-1, 1)

    if by == b'<':
        return 'xml'
    else:
        return 'json'


class Writer:
    """Write metrics to a file descriptor in statsfile format.
    API example::

        >>> meta = {'time': '2015-08-06T23:54:48.771150'}
        >>> metrics = {'literals_unique_count': 26816}
        >>> with open("demo.xml.stats", "wb") as fd:
        ...     writer = cnfanalysis.statsfile.Writer(fd, 'xml', 'utf-8')
        ...     writer.write(meta, metrics)
        ...     # or more: writer.write(meta2, metrics2)
        ...     writer.finish()
    """

    def __init__(self, fd, format='json', encoding='utf-8'):
        if format.lower() == 'xml':
            self.writer = XmlWriter(fd, encoding=encoding)
        else:
            self.writer = JsonWriter(fd, encoding=encoding)

    def write(self, meta, metrics):
        self.writer.write(meta, metrics)

    def finish(self):
        self.writer.finish()


class XmlWriter:
    """Write an XML incrementally. Uses the basic idea of SAX XML APIs,
    but specifically writes down metrics.

    Example::

        >>> with open('example.xml.stats', 'wb') as fd:
        ...     writer = XmlWriter(fd, encoding='utf-8')
        ...     for meta, metrics in analyzed_filemetrics:
        ...         writer.write(meta, metrics)
        ...     writer.finish()
    """
    root = 'metrics'

    def __init__(self, filedescriptor, *, encoding='utf-8'):
        self.gen = xml.sax.saxutils.XMLGenerator(filedescriptor,
            encoding=encoding, short_empty_elements=True)
        self.first = True

    def start(self):
        self.gen.startDocument()
        self.gen.startElement(self.root, {})
        self.gen.ignorableWhitespace("\n  ")
        return self

    def write(self, meta, metrics):
        """Write one pair of meta data and metrics to the XML file"""
        if self.first:
            self.start()
            self.first = False

        self.gen.startElement('file', meta)
        self.gen.ignorableWhitespace("\n    ")

        if metrics:
            count = len(metrics)
            for key, value in metrics.items():
                self.gen.startElement('metric', {key: str(value)})
                self.gen.endElement('metric')

                if count != 1:
                    self.gen.ignorableWhitespace("\n    ")
                else:
                    self.gen.ignorableWhitespace("\n  ")
                count -= 1

        self.gen.endElement('file')
        self.gen.ignorableWhitespace("\n")

    def finish(self):
        self.gen.endElement(self.root)
        self.gen.ignorableWhitespace("\n")
        self.gen.endDocument()


class JsonWriter:
    """Write a JSON incrementally. Applies the idea of SAX XML APIs to JSON
    to specifically writes down metrics.

    Example::

        >>> with open('example.json.stats', 'wb') as fd:
        ...     writer = XmlWriter(fd, encoding='utf-8')
        ...     for meta, metrics in analyzed_filemetrics:
        ...         writer.write(meta, metrics)
        ...     writer.finish()
    """

    def __init__(self, filedescriptor, *, encoding='utf-8'):
        self.fd = filedescriptor
        self.enc = encoding
        self.first = True

    def start(self):
        self.fd.write('{\n  "metrics": [\n    '.encode(self.enc))

    def write(self, meta, metrics):
        """Write a metric to the JSON file"""
        if self.first:
            self.start()
            self.first = False
        else:
            self.fd.write(',\n    '.encode(self.enc))

        layouted = {}
        for attr, val in meta.items():
            layouted[attr] = val
        layouted['metric'] = metrics

        obj = json.dumps(layouted, indent=2, sort_keys=True).replace('\n', '\n    ')
        self.fd.write(obj.encode(self.enc))

    def finish(self):
        self.fd.write('\n  ]\n}\n'.encode(self.enc))


def Reader(fd, format='?', encoding='utf-8'):
    """Read metadata & metrics from a file descriptor.

    Remark: The file descriptor is expected to be opened in binary mode.
    Remark: For format=xml, the encoding is ignored
    Remark: For format=?, detect_format is invoked to determine the 'xml' or 'json'

    API example::

        >>> with open("demo.xml.stats") as fd:
        ...     reader = cnfanalysis.statsfile.Reader(fd, 'xml')
        ...     for meta, metrics in reader:
        ...         print(meta, metrics)
    """
    if format == '?':
        format = detect_format(fd)
    if format.lower() == 'xml':
        return XmlReader(fd)
    else:
        return JsonWriter(fd, encoding=encoding)


def XmlReader(filedescriptor):
    """Read a stats XML file and provide meta-metrics pairs as iterator

    Example::

        >>> with open('example.xml.stats', 'rb') as fd:
        ...     reader = XmlReader(fd)
        ...     for meta, metrics in reader:
        ...         print(meta, metrics)
    """
    meta, metrics = {}, {}
    for (event, elem) in xml.etree.ElementTree.iterparse(what, events=['start', 'end']):
        if event == 'start' and elem.tag == 'file':
            for attr, val in elem.attrib.items():
                meta[attr] = val
        elif event == 'start' and elem.tag == 'metric':
            for attr, val in elem.attrib.items():
                metrics[attr] = val
        elif event == 'end' and elem.tag == 'file':
            yield meta, metrics
            meta, metrics = {}, {}


def JsonReader(filedescriptor, encoding='utf-8'):
    """Read a stats JSON file and provide meta-metrics pairs as iterator.
    Loads full file in memory. Might change in the future.

    Remark: To be consistent with the XML API, filedescriptor is expected
    to be opened in *binary* mode and an encoding parameter must be provided.

    TODO: Use jsaone?
    TODO: Build Python API for rapidjson?

    Example::

        >>> with open('example.json.stats', 'rb') as fd:
        ...     reader = JsonReader(fd, 'utf-8')
        ...     for meta, metrics in reader:
        ...         print(meta, metrics)
    """
    whole = filedescriptor.read().decode(encoding)
    complete = json.loads(whole, parse_float=float, parse_int=int)
    for obj in complete['metrics']:
        meta, metrics = {}, {}

        for attr, val in obj:
            if attr == 'metric':
                metrics = val
            else:
                meta[attr] = val

        yield meta, metrics

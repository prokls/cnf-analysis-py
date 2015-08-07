#!/usr/bin/env python3

"""
    cnf-analysis.output
    ===================

    Write CNF metrics to file descriptor.

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import io
import _io
import sys
import json
import xml.dom.minidom
import xml.etree.ElementTree


class Writer:
    def __init__(self, fp: _io.TextIOWrapper, *, encoding: str):
        pass

    def receive(self, key, value):
        pass

    def write(self):
        pass


class XMLWriter(Writer):
    """Receive a list of metrics and write XML representation
    to specified file descriptor.
    """

    def __init__(self, fp: _io.TextIOWrapper, *, encoding: str):
        self.fp = fp
        self.encoding = encoding
        self.metrics = {}

    def receive(self, key, value):
        self.metrics[key] = value

    def write(self):
        Element = xml.etree.ElementTree.Element
        metrics_elem = Element('metrics')
        file_elem = Element('file')
        
        for key, value in self.metrics.items():
            if key.startswith('@'):
                file_elem.attrib[key[1:]] = value
            else:
                metric_elem = Element('metric')
                metric_elem.attrib[key] = str(value)
                file_elem.append(metric_elem)

        metrics_elem.append(file_elem)

        output = io.BytesIO()
        tree = xml.etree.ElementTree.ElementTree(metrics_elem)
        tree.write(output, encoding=self.encoding, xml_declaration=True)
        
        # dirty hack to achieve pretty printing
        doc = xml.dom.minidom.parseString(output.getvalue())
        blob = doc.toprettyxml(encoding=self.encoding)

        if self.fp == sys.stdout:
            self.fp.write(blob.decode(self.encoding))
        else:
            self.fp.write(blob)


class JSONWriter(Writer):
    """Take a list of metrics and write JSON representation
    to specified file descriptor.
    """

    def __init__(self, fp: _io.TextIOWrapper, *, encoding: str):
        self.fp = fp
        self.encoding = encoding
        self.metrics = {}

    def receive(self, key, value):
        self.metrics[key] = value

    def write(self):
        data = {'metric': {}}

        for key, value in self.metrics.items():
            if key.startswith('@'):
                data[key[1:]] = value
            else:
                data['metric'][key] = value

        blob = json.dumps({'metrics': [data]}, indent=2)
        if self.fp == sys.stdout:
            print(blob)
            print()
        else:
            self.fp.write(blob.encode(self.encoding) + b'\n')

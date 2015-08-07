#!/usr/bin/env python3

"""
    cnf-analysis-combiner
    =====================

    Given several metrics specification files (eg. JSON here) such as::

        {"metric":{"count_unique_variables": 13408,"count_existential_literals": 0, …}}

    combine them into one metrics specification file::

        {"metrics":
          {"metric":{"count_unique_variables": 13408,"count_existential_literals": 0, …}},
          {"metric":{"count_unique_variables": 1283,"count_existential_literals": 0, …}}}

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import io
import sys
import json
import argparse
import collections
import xml.dom.minidom
import xml.sax.saxutils
import xml.etree.ElementTree

import processing

METRICS = processing.METRICS
BATCH_SIZE = 50

Metrics = collections.namedtuple("Metrics",
    [key for key, value in METRICS.items() if value[0]]
)


def read_xml_file(blob: bytes, encoding: str) -> (str, str, str, Metrics):
    tree = xml.etree.fromstring(blob)
    data = {}

    for fileelem in tree.xpath('/metrics/file'):
        filename = fileelem.attrib['filename']
        time = fileelem.attrib['time']
        sha1sum = fileelem.attrib['sha1sum']

        for metric_elem in fileelem.xpath('metric'):
            for attr in metric_elem.attrib:
                data[attr] = metric_elem.attrib[attr]

    return (filename, sha1sum, time, data)


def read_json_file(blob: bytes, encoding: str) -> (str, str, str, Metrics):
    obj = json.loads(blob.decode(encoding))['metrics'][0]

    metric = {}
    for key, value in obj['metric'].items():
        if key in METRICS and METRICS[key][0]:
            metric[key] = value

    metrics = Metrics(**metric)
    return (obj['filename'], obj['sha1sum'], obj['time'], metrics)


def read_single_file(filepath: str, encoding: str) -> (str, str, str, Metrics):
    with open(filepath, 'rb') as fp:
        content = fp.read()
        if content[0] == b'<':
            return read_xml_file(content, encoding)
        else:
            return read_json_file(content, encoding)


def to_xml(filepath: str, metrics: [(str, str, str, Metrics)], encoding: str):
    Element = xml.etree.ElementTree.Element
    metrics_elem = Element('metrics')

    for m in metrics:
        file_elem = Element('file')
        file_elem.attrib['filename'] = m[0]
        file_elem.attrib['sha1sum'] = m[1]
        file_elem.attrib['time'] = m[2]

        for attr in m[3]._fields:
            metric_elem = Element('metric')
            metric_elem.attrib[attr] = str(getattr(m[3], attr))
            file_elem.append(metric_elem)

        metrics_elem.append(file_elem)

    output = io.BytesIO()
    tree = xml.etree.ElementTree.ElementTree(metrics_elem)
    tree.write(output, encoding=encoding, xml_declaration=True)
    
    # dirty hack to achieve pretty printing
    doc = xml.dom.minidom.parseString(output.getvalue())
    blob = doc.toprettyxml(encoding=encoding)

    if filepath == '-':
        print(blob.decode(encoding))
    else:
        with open(filepath, 'wb') as fp:
            fp.write(blob)


def to_json(filepath: str, metrics: [(str, str, str, Metrics)], encoding: str):
    obj = { 'metrics': [] }

    for m in metrics:
        fileobj = { 'filename': m[0], 'sha1sum': m[1], 'time': m[2] }
        fileobj['metric'] = vars(m[3])
        obj['metrics'].append(fileobj)

    if filepath == '-':
        print(json.dumps(obj, sort_keys=True, indent=2))
    else:
        with open(filepath, 'wb') as fp:
            json.dump(obj, fp, sort_keys=True, indent=2).encode(encoding)


def main(args: argparse.Namespace) -> int:
    # TODO: use batchwise cache such that at most BATCH_SIZE instances are stored
    cache = []

    for i, inputfile in enumerate(args.inputfiles):
        data = read_single_file(inputfile, args.input_encoding)
        cache.append(data)

    if args.format == 'xml':
        to_xml(args.output, cache, args.output_encoding)
    else:
        to_json(args.output, cache, args.output_encoding)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine CNF analysis results')

    parser.add_argument('inputfiles', metavar='inputfiles', nargs='+',
                        help='files to read metrics from and combine')
    parser.add_argument('-o', '--output', dest='output', default='-',
                        help='output filepath (default: stdout)')
    parser.add_argument('-u', '--input-encoding', dest='input_encoding', default='utf-8',
                        help='input encoding (default: utf-8)')
    parser.add_argument('-e', '--output-encoding', dest='output_encoding', default='utf-8',
                        help='output encoding (default: utf-8)')
    parser.add_argument('-f', '--format', default='json',
                        help='output format (default: json)')

    args = parser.parse_args()
    sys.exit(main(args))

#!/usr/bin/env python3

"""
    cnf-analysis-combiner
    =====================

    Given several metrics specification files (eg. JSON here) such as::

        {"metrics":
          {"metric":{"count_unique_variables": 13408,"count_existential_literals": 0, …}}
        }

    combine them into one metrics specification file::

        {"metrics":
          {"metric":{"count_unique_variables": 13408,"count_existential_literals": 0, …}},
          {"metric":{"count_unique_variables": 1283,"count_existential_literals": 0, …}}},
          …
        }

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

import statsfile


class XMLWriter:
    def __init__(self, filepath, encoding='utf-8'):
        self.filepath = filepath
        self.encoding = encoding

    def __enter__(self):
        self.fp = open(self.filepath, 'wb')
        content = self.fp.read()

        if self.input_format.lower() == 'xml':
            self.metrics = from_xml_file(content, self.input_encoding)
        else:
            self.metrics = from_json_file(content, self.input_encoding)

        return self.metrics

    def __exit__(self, type, value, traceback):
        failed = (traceback is not None)
        try:
            self.fp.close()
        except Exception:
            failed = True

        if self.output_format == 'xml':
            to_xml(self.metrics, self.output_file, self.output_encoding)
        else:
            to_json(self.metrics, self.output_file, self.output_encoding)

        if failed:
            print('FAIL ' + self.output_file, file=sys.stderr)
        else:
            print('OKAY ' + self.output_file, file=sys.stderr)
        return True



class JSONWriter:
    def __init__(self, filepath, encoding='utf-8'):
        self.filepath = filepath
        self.first_object = True
        self.encoding = encoding

    def __enter__(self):
        self.fp = open(self.filepath, 'wb')
        self.fp.write(b'{\n  "metrics": [\n')
        return self

    def __exit__(self, type, value, traceback):
        self.fp.write(b'\n  ]\n}\n')
        self.fp.close()

        print('OKAY ' + self.filepath, file=sys.stderr)
        return True

    def write(self, meta: dict, metric: dict):
        if not self.first_object:
            self.fp.write(b',\n')
        obj = meta
        obj['metric'] = metric
        strrepr = json.dumps(obj, indent=2, sort_keys=True).replace('\n', '    ')
        self.fp.write(strrepr.encode(self.encoding))
        self.first_object = False





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
    """Main routine."""
    if args.output_format == 'json':
        Writer = JSONWriter
    else:
        Writer = XMLWriter

    with Writer(args.outfile, encoding=args.output_encoding) as writer:
        for inputfile in args.inputfiles:
            if statsfile.detect_format(inputfile) == 'xml':
                Reader = XMLReader
            else:
                Reader = JSONReader

            with Reader(inputfile) as reader:
                for (meta, metric) in reader:
                    writer.write(meta, metric)

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine CNF analysis results')

    parser.add_argument('inputfiles', metavar='inputfiles', nargs='+',
                        help='files to read metrics from and combine')
    parser.add_argument('-o', '--output', dest='outputfile', default='-',
                        help='output filepath (default: stdout)')
    parser.add_argument('-u', '--input-encoding', dest='input_encoding', default='utf-8',
                        help='input encoding for all files (default: utf-8)')
    parser.add_argument('-e', '--output-encoding', dest='output_encoding', default='utf-8',
                        help='output encoding (default: utf-8)')
    parser.add_argument('-f', '--output-format', dest='output_format', default='json',
                        help='output format (default: json)')

    args = parser.parse_args()
    sys.exit(main(args))

#!/usr/bin/env python3

"""
    cnfanalysis.stats
    -----------------

    Library to handle featurefiles.

    (C) 2015/2016, CC-0 licensed, Lukas Prokop
"""

import json
import os.path
import hashlib
import datetime

import xml.dom.minidom
import xml.etree.ElementTree

import xml.sax.saxutils
import xml.sax.handler


def detect_format(filepath):
    """Given a featuresfile of unknown format.
    Detect the format by reading the first byte.

    Feature: File descriptors as argument work also

    :param filepath:        Read one byte from this filepath to detect format
    :type filepath:         str
    :return:                'xml', 'json' or None (empty file)
    :rtype:                 str | None
    """
    if filepath.endswith('.stats.xml'):
        return 'xml'
    if filepath.endswith('.stats.json'):
        return 'json'

    try:
        with open(filepath, 'r') as fp:
            by = fp.read(1)
    except TypeError:
        # assume filepath is file descriptor
        by = fp.read(1)
        fp.seek(-1, 1)

    if by == b'<':
        return 'xml'
    elif by == b'':
        return None
    else:
        return 'json'


def md5sha1hashes(sourcefile, blocksize=4096):
    """Compute MD5 and SHA1 digests simultaneously of the file
    given at filepath `sourcefile`

    :param sourcefile:      source file path
    :type sourcefile:       str
    :param blocksize:       blocksize for blockwise reading
    :type blocksize:        int
    :return:                MD5 digest, SHA1 digest
    :rtype:                 (str, str)
    """
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    with open(sourcefile, 'rb') as fd:
        buf = fd.read(blocksize)
        while len(buf):
            md5.update(buf)
            sha1.update(buf)
            buf = fd.read(blocksize)
        return (md5.hexdigest(), sha1.hexdigest())


def cnf2hash(sourcefile, blocksize=4096):
    """Compute cnfhash of given CNF files"""
    import cnfhash

    def read_blockwise(filepath):
        with open(filepath, 'rb') as fd:
            while True:
                buf = fd.read(blocksize)
                if len(buf) == 0:
                    break
                yield buf

    return cnfhash.hash_dimacs(read_blockwise(sourcefile))


def extend_metadata(feature_data, sourcefile='', fullpath=False, hashes=False):
    """Given `feature_data`, extend this dictionary to a full-featured
    dictionary with metadata.

    :param feature_data:    Feature data
    :type feature_data:     dict
    :param sourcefile:      filepath to source file
    :type sourcefile:       str
    :param fullpath:        shall I store the full path in JSON?
    :type fullpath:         bool
    :param hashes:          shall I compute hashes for this file?
    :type hashes:           bool
    :return:                a dictionary with feature data and meta data
    :rtype:                 dict
    """
    data = [{
        "@timestamp": datetime.datetime.utcnow().isoformat(),
        "@version": "1.0.0",
        "featuring": feature_data
    }]
    if not fullpath:
        data[0]["@filename"] = os.path.basename(sourcefile)

    if sourcefile and os.path.exists(sourcefile):
        if fullpath:
            data[0]["@filename"] = sourcefile
        else:
            data[0]["@filename"] = os.path.basename(sourcefile)
        if hashes:
            md5sum, sha1sum = md5sha1hashes(sourcefile)
            data[0]["@md5sum"] = md5sum
            data[0]["@sha1sum"] = sha1sum
            data[0]["@cnfhash"] = cnf2hash(sourcefile)

    return data


def write_json(filepath, feature_data, sourcefile='', fullpath=False,
               hashes=False, mode='x', meta={}):
    """Given a dictionary of `featuredata`, store it at `filepath`
    in JSON format.

    :param filepath:        filepath at filesystem
    :type filepath:         str
    :param feature_data:    associations of feature name to value
    :type feature_data:     dict
    :param sourcefile:      filepath to source file
    :type sourcefile:       str
    :param fullpath:        shall I store the full path in JSON?
    :type fullpath:         bool
    :param hashes:          shall I compute hashes for this file?
    :type hashes:           bool
    :param mode:            file mode to use for writing
    :type mode:             str
    :param meta:            meta attributes to overwrite metadata
    :type meta:             dict
    """
    data = extend_metadata(feature_data, sourcefile, fullpath, hashes)
    data[0].update(meta)

    with open(filepath, mode, encoding='utf-8') as fd:
        json.dump(data, fd, indent=2, sort_keys=True)
        fd.write('\n')


def write_xml(filepath, feature_data, sourcefile='', fullpath=False, hashes=False, mode='xb'):
    """Given a dictionary of `feature_data`, store it at `filepath`
    in XML format.

    :param filepath:        filepath at filesystem
    :type filepath:         str
    :param feature_data:    associations of feature name to value
    :type feature_data:     dict
    :param sourcefile:      filepath to source file
    :type sourcefile:       str
    :param fullpath:        shall I store the full path in XML?
    :type fullpath:         bool
    :param hashes:          shall I compute hashes for this file?
    :type hashes:           bool
    :param mode:            file mode to use for writing
    :type mode:             str
    """
    data = extend_metadata(feature_data, sourcefile, fullpath, hashes)

    with open(filepath, mode) as fd:
        doc = xml.sax.saxutils.XMLGenerator(fd, encoding='utf-8',
                                            short_empty_elements=True)
        doc.startDocument()
        doc.startElement('features', {})
        doc.ignorableWhitespace("\n  ")

        meta = dict((k[1:], v) for k, v in data[0].items() if k != 'featuring')
        doc.startElement('file', meta)

        for name, value in data[0]['featuring'].items():
            doc.ignorableWhitespace("\n    ")
            doc.startElement('featuring', {name: str(value)})
            doc.endElement('featuring')

        doc.ignorableWhitespace("\n  ")
        doc.endElement('file')
        doc.ignorableWhitespace("\n")

        doc.endElement('features')
        doc.ignorableWhitespace("\n")
        doc.endDocument()


def read(filepath, fmt=None):
    """Read a ``featuresfile`` from the given `filepath`. Name the format
    ('xml' or 'json') if it is known.

    :param filepath:    filepath to source file
    :type filepath:     str
    :param fmt:         format: 'xml', 'json' or None (= unknown)
    :type fmt:          str
    :return:            a list of dictionaries containing metadata and features,
                        might also be a generator
    :rtype:             [dict]
    """
    if fmt is None:
        fmt = detect_format(filepath)
    if fmt is None:
        raise IOError('Cannot read features form empty file {}'.format(filepath))

    if fmt == 'json':
        return read_json(filepath)
    else:
        return read_xml(filepath)


def read_json(filepath):
    """Read a ``featuresfile`` in JSON format from given `filepath`.

    :param filepath:    filepath to source file
    :type str:          str
    :return:            a list of dictionaries containing metadata and features
    :rtype:             [dict]
    """
    with open(filepath, encoding='utf-8') as fd:
        return json.load(fd)


def read_xml(filepath):
    """Read a ``featuresfile`` in XML format from given `filepath`.

    :param filepath:    filepath to source file
    :type str:          str
    :return:            a generator of dictionaries containing metadata and features
    :rtype:             generator of dicts
    """
    try:
        for (event, elem) in xml.etree.ElementTree.iterparse(filepath, events=['start', 'end']):
            if event == 'start' and elem.tag == 'features':
                features = {}
            elif event == 'start' and elem.tag == 'file':
                for attr, val in elem.attrib.items():
                    features['@' + attr] = val
            elif event == 'start' and elem.tag == 'featuring':
                for attr, val in elem.attrib.items():
                    features[attr] = val
            elif event == 'end' and elem.tag == 'file':
                yield features
                features = {}
    except Exception:
        raise ValueError("Invalid features file XML structure in {}".format(filepath))

#!/usr/bin/env python3

"""
    cnf-analysis-annotate
    =====================

    Given a set of cnf-analysis stats files.
    Annotate them with additional values for given keys::

        ./annotate.py --key=@category --value=satcomp2014,verification test.cnf.stats

    This command would add the value ``'satcomp2014,verification'`` to the key
    ``'category'`` in the stats file ``test.cnf.xml``. The @ symbol denotes
    a meta key (not some metric, but meta information like ``time`` or ``sha1sum``)::

        {
          "metrics": [
            {
              "category": "satcomp2014,verification",
              "time": "2015-08-07T00:50:46.290754",
              …

    Or in XML::

        $ ./annotate.py -f xml --key=@category --value=satcomp2014,verification test.cnf.stats

        <metrics>
          <file category="satcomp2014,verification" time="2015-08-07T00:50:46.290754">
          …

    Per default an exception will be raised if some ``--key`` already exists.
    You can supply ``-a`` to append the given values to existing values.

    Per default the tool generates a ``{filename}.modified`` file. You can annotate
    files in-place by supplying the ``-i`` option (actually it will use a temporary file
    and then overwrite the original file).

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import sys
import shutil
import os.path
import argparse
import tempfile
import cnfanalysis


def update_dictionary(original: dict, update: dict, append=False):
    """Update a dictionary `original` with the provided data `update`

        >>> data = {'hello': 'world'}
        >>> update_dictionary(data, {'hello': '!'}, append=True)
        >>> data
        {'hello': 'world!'}
        >>> update_dictionary(data, {'foo': 'bar'}, append=False)
        >>> data
        {'hello': 'world!', 'foo': 'bar'}
    """
    for attr, val in update.items():
        if attr in original and append:
            original[attr] = val + update[attr]
        elif attr in original and not append:
            raise KeyError("Key {} already exists. I won't overwrite")
        elif attr not in original:
            original[attr] = update[attr]


def update_file_inplace(inputfile, format, meta, metrics, output_format='?',
    append=False, input_encoding='utf-8', output_encoding='utf-8'):
    """Update the metadata & metrics in the given file

    :param inputfile:       the file to update
    :type inputfile:        str
    :param format:          input file format; '?' (= guess), 'xml' or 'json'
    :type format:           str
    :param meta:            Metadata to update
    :type meta:             dict
    :param metrics:         Metrics to update
    :type metrics:          dict
    :param output_format:   output file format; 'xml' or 'json'
    :param append:          append to existing keys instead of throwing an exception
    :param input_encoding:  encoding of `inputfile`
    :param output_encoding: encoding of {filename}.modified or `inputfile` (`inplace`)
    """
    handle, filepath = tempfile.mkstemp(prefix='cnfanalysis')

    with open(inputfile, 'rb') as fd_r:
        reader = cnfanalysis.statsfile.Reader(fd_r, format, input_encoding)

        with handle as fd_w:
            writer = cnfanalysis.statsfile.Writer(fd_w,
                output_format, output_encoding)

            for original_meta, original_metrics in reader:
                update_dictionary(original_meta, meta, append=append)
                update_dictionary(original_metrics, metrics, append=append)

                writer.write(original_meta, original_metrics)

    shutil.move(filepath, inputfile)


def update_file(inputfile, format, meta, metrics, output_format='?',
    append=False, input_encoding='utf-8', output_encoding='utf-8'):
    """Update the metadata & metrics in the given file

    :param inputfile:       the file to update
    :type inputfile:        str
    :param format:          input file format; '?' (= guess), 'xml' or 'json'
    :type format:           str
    :param meta:            Metadata to update
    :type meta:             dict
    :param metrics:         Metrics to update
    :type metrics:          dict
    :param output_format:   output file format; 'xml' or 'json'
    :param append:          append to existing keys instead of throwing an exception
    :param input_encoding:  encoding of `inputfile`
    :param output_encoding: encoding of {filename}.modified or `inputfile` (`inplace`)
    """
    outputfile = inputfile + '.modified'
    if os.path.exists(outputfile):
        raise IOError('File already exists: {}'.format(outputfile))

    with open(inputfile, 'rb') as fd_r:
        reader = cnfanalysis.statsfile.Reader(fd_r, format, input_encoding)

        with open(outputfile, 'wb') as fd_w:
            writer = cnfanalysis.statsfile.Writer(fd_w,
                output_format, output_encoding)

            for original_meta, original_metrics in reader:
                update_dictionary(original_meta, meta, append=append)
                update_dictionary(original_metrics, metrics, append=append)

                writer.write(original_meta, original_metrics)

    print('{} has been written.'.format(outputfile))


def validate_parameters(args: argparse.Namespace):
    """Validate CLI arguments.

    :param args:        argparse namespace of the CLI arguments
    """
    if len(args.key) != len(args.value):
        raise argparse.ArgumentError("You must provide as many --key as --value")


def main(args: argparse.Namespace) -> int:
    """Main routine"""
    validate_parameters(args)

    opts = {
        'input_encoding': args.input_encoding,
        'output_encoding': args.output_encoding,
        'output_format': args.format
    }
    meta, metrics = {}, {}
    for i in range(len(args.key)):
        if args.key[i].startswith('@'):
            meta[args.key[i][1:]] = args.value[i]
        else:
            metrics[args.key[i]] = args.value[i]

    for inputfile in args.inputfiles:
        format = 'xml' if '.xml' in inputfile else '?'
        format = 'json' if '.json' in inputfile else format

        if args.output_format == '?':
            output_format = format
        else:
            output_format = args.output_format

        if args.inplace:
            update_file_inplace(inputfile, format, meta, metrics,
                output_format=output_format, append=args.append,
                input_encoding=args.input_encoding,
                output_encoding=args.output_encoding)
        else:
            update_file(inputfile, format, meta, metrics,
                output_format=output_format, append=args.append,
                input_encoding=args.input_encoding,
                output_encoding=args.output_encoding)

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine CNF analysis results')

    parser.add_argument('inputfiles', metavar='inputfiles', nargs='+',
                        help='files to read metrics from and combine')
    parser.add_argument('--key', action='append', required=True,
                       help='the name of the meta key')
    parser.add_argument('--value', action='append', required=True,
                       help='the comma-separated list of values to add')
    parser.add_argument('-a', '--append', action='store_true',
                       help='append mode; append to existing keys instead of erroring')
    parser.add_argument('-u', '--input-encoding', dest='input_encoding', default='utf-8',
                        help='input encoding (default: utf-8)')
    parser.add_argument('-e', '--output-encoding', dest='output_encoding', default='utf-8',
                        help='output encoding (default: utf-8)')
    parser.add_argument('-f', '--output-format', dest='format', default='?',
                        help='output format (default: same as all input files)')
    parser.add_argument('-i', '--inplace', dest='inplace', action='store_true',
                        help='process files inplace, do not create .modified files')

    args = parser.parse_args()
    sys.exit(main(args))

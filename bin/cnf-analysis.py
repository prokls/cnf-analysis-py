#!/usr/bin/env python3

"""
    cnf-analysis
    ============

    Analyse files specifying a CNF.
    Supports
    - the DIMACS file format
    - the IPASIR interface [0]

    [0] http://baldur.iti.kit.edu/sat-race-2015/index.php?cat=rules#api

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import sys
import os.path
import argparse

import cnfanalysis.input
import cnfanalysis.processing
import cnfanalysis.output

__version__ = '1.7.0'
__author__ = 'Lukas Prokop <lukas.prokop@student.tugraz.at>'


def main(args: argparse.Namespace) -> int:
    """Analyze files individually into several metrics datasets"""
    if args.description:
        print(processing.METRICS_DOCUMENTATION)
        return 0

    # prepare arguments
    dimacsfiles = args.dimacsfiles
    read_stdin = False

    if '-' in args.dimacsfiles:
        read_stdin = True
    if len(args.dimacsfiles) == 0:
        read_stdin = True
        dimacsfiles = ['-']

    if read_stdin:
        print('No DIMACS filepaths provided. Expecting DIMACS content at stdin …', file=sys.stderr)

    # abstract reader, processing and writer
    if args.multiline:
        read = cnfanalysis.input.read_multiline_dimacs
    else:
        read = cnfanalysis.input.read_dimacs
    Processor = processing.IpasirAnalyzer
    Writer = output.XMLWriter if args.format.lower() == 'xml' else output.JSONWriter
    if args.format not in ['xml', 'json']:
        print("Warning: Unknown format '{}'. JSON taken as output format.".format(args.format))

    # read, process and write
    for dimacsfile in dimacsfiles:
        if dimacsfile != '-' and args.skip:
            if os.path.exists(dimacsfile + '.stats') and not os.stat(dimacsfile + '.stats').st_size == 0:
                print('Info: File {} already exists. Skipping.' \
                    .format(dimacsfile + '.stats'), file=sys.stderr)
                continue

        if dimacsfile == '-':
            writer = Writer(sys.stdout, encoding=args.encoding)
            analyzer = Processor(writer)
            read(sys.stdin, analyzer, ignoreheader=args.ignoreheader)
            analyzer.solve()
            analyzer.release()
            writer.write()
        elif args.stdout:
            with open(dimacsfile) as fp:
                writer = Writer(sys.stdout, encoding=args.encoding)
                analyzer = Processor(writer, filepath=dimacsfile)
                read(fp, analyzer, ignoreheader=args.ignoreheader)
                analyzer.solve()
                analyzer.release()
                writer.write()
        else:
            with open(dimacsfile) as fp:
                try:
                    with open(dimacsfile + '.stats', 'wb') as fp2:
                        writer = Writer(fp2, encoding=args.encoding)
                        analyzer = Processor(writer, filepath=dimacsfile)
                        read(fp, analyzer, ignoreheader=args.ignoreheader)
                        analyzer.solve()
                        analyzer.release()
                        writer.write()
                        print("Info: File '{}' written".format(dimacsfile + '.stats', file=sys.stderr))
                except Exception as e:
                    os.unlink(dimacsfile + '.stats')
                    raise e
                except KeyboardInterrupt:
                    os.unlink(dimacsfile + '.stats')
                    raise KeyboardInterrupt

        del writer
        del analyzer

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CNF analysis')

    parser.add_argument('dimacsfiles', metavar='dimacsfiles', nargs='*',
                        help='filepath of DIMACS file')
    parser.add_argument('-e', '--encoding', dest='encoding', default='utf-8',
                        help='output encoding (default: utf-8)')
    parser.add_argument('-f', '--format', dest='format', default='json',
                        help='output format (default: json)')
    parser.add_argument('-p', '--ignore-header', dest='ignoreheader', action='store_true',
                        help='do not check validity of header lines (default: false)')
    parser.add_argument('-m', '--multiline', dest='multiline', action='store_true',
                        help='parse DIMACS file in multiline mode (default: false)')
    parser.add_argument('--stdout', action='store_true',
                        help='write to stdout instead of files (always set if stdin is used)')
    parser.add_argument('--description', action='store_true',
                        help='do nothing but print documentation of metrics')
    parser.add_argument('--skip-existing', dest='skip', action='store_true',
                        help='Skip analysis if file with extension .stats already exists')

    args = parser.parse_args()
    sys.exit(main(args))

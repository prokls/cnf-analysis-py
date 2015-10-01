#!/usr/bin/env python

"""
    cnfanalysis.scripts
    ~~~~~~~~~~~~~~~~~~~

    Entry point for all python scripts.

    (C) 2015, meisterluk, BSD 3-clause license
"""

import sys
import os.path
import argparse

from . import processing
from . import statsfile
from . import dimacsfile

__version__ = '1.7.0'
__author__ = 'Lukas Prokop <lukas.prokop@student.tugraz.at>'


def run(args: argparse.Namespace) -> int:
    """Analyze files individually into several metrics datasets"""
    if args.description:
        print(processing.METRICS_DOCUMENTATION)
        return 0

    def create_new_filename(path: str, format: str) -> str:
        base, ext = os.path.splitext(path)
        if ext == ".cnf":
            return "{}.stats.{}".format(base, format)
        else:
            return "{}.stats.{}".format(path, format)

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
        read = dimacsfile.read_multiline
    else:
        read = dimacsfile.read
    Processor = processing.IpasirAnalyzer
    if args.format not in {'xml', 'json'}:
        print("Warning: Unknown format '{}'. JSON taken as output format.".format(args.format))

    # read, process and write
    for srcfile in dimacsfiles:
        outformat = 'xml' if args.format == 'xml' else 'json'
        outfile = create_new_filename(srcfile, outformat)

        if srcfile != '-' and args.skip:
            if os.path.exists(outfile) and not os.stat(outfile).st_size == 0:
                print('Info: File {} already exists. Skipping.' \
                    .format(outfile), file=sys.stderr)
                continue

        if srcfile == '-':
            writer = statsfile.Writer(sys.stdout, format=outformat, encoding=args.encoding)
            analyzer = Processor(writer)
            read(sys.stdin, analyzer, ignoreheader=args.ignoreheader)
            analyzer.solve()
            analyzer.release()
            writer.write()
        elif args.stdout:
            with open(srcfile) as fp:
                writer = statsfile.Writer(sys.stdout, format=outformat, encoding=args.encoding)
                analyzer = Processor(writer, filepath=srcfile)
                read(fp, analyzer, ignoreheader=args.ignoreheader)
                analyzer.solve()
                analyzer.release()
                writer.write()
        else:
            with open(srcfile) as fp:
                try:
                    with open(outfile, 'wb') as fp2:
                        writer = statsfile.Writer(fp2, format=outformat, encoding=args.encoding)
                        analyzer = Processor(writer, filepath=srcfile)
                        read(fp, analyzer, ignoreheader=args.ignoreheader)
                        analyzer.solve()
                        analyzer.release()
                        print("Info: File '{}' written".format(outfile, file=sys.stderr))
                except Exception as e:
                    os.unlink(outfile)
                    raise e
                except KeyboardInterrupt:
                    os.unlink(outfile)
                    raise KeyboardInterrupt

        del writer
        del analyzer

    return 0



def main():
    """Main routine"""
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
    sys.exit(run(args))


if __name__ == '__main__':
    main()

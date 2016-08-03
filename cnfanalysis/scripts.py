#!/usr/bin/env python3

"""
    cnfanalysis.scripts
    -------------------

    Convenient functions for perform tasks with cnfanalysis.

    (C) 2015-2016, CC-0, Lukas Prokop
"""

import sys
import os.path
import argparse
import multiprocessing

from . import dimacs
from . import collect
from . import stats


def main():
    parser = argparse.ArgumentParser(description='CNF analysis')
    parser.add_argument('dimacsfiles', metavar='dimacsfiles', nargs='+',
                        help='filepath of DIMACS file')
    parser.add_argument('-f', '--format', choices={'json', 'xml'}, default='json',
                        help='format to store feature data in')
    parser.add_argument('--ignore', action='append',
                        help='a prefix for lines that shall be ignored (like "c")')
    parser.add_argument('-n', '--no-hashes', action='store_true',
                        help='do not compute hashes for the CNF file considered')
    parser.add_argument('-p', '--fullpath', action='store_true',
                        help='use full path instead of basename in featurefiles')
    parser.add_argument('-s', '--skip-existing', action='store_true',
                        help='skip file if file.stats.json exists')

    # TODO: support gzipped files
    # TODO: drop md5/sha2 because cnfhash is stable?!

    def derive_outfile(filepath, fmt):
        base, ext = filepath.rsplit('.', 1)
        if ext == 'gz':
            base, ext = base.rsplit('.', 1)
        return base + '.stats.' + fmt

    args = parser.parse_args()
    arguments = [args.format, ''.join(args.ignore or ['%', 'c']), args.fullpath, not args.no_hashes, args.skip_existing]
    with multiprocessing.Pool(os.cpu_count() or 1) as p:
        p.starmap(evaluate_file, [[i, derive_outfile(i, args.format)] + arguments for i in args.dimacsfiles])


def evaluate_file(filepath, *args, **kwargs):
    oldpath = os.path.splitext(filepath)[0] + ".stats.json"
    if os.path.exists(oldpath):
        skip_existing = args[5]
        if skip_existing:
            return
        else:
            import datetime
            import shutil
            backupsuffix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            newname = "{}.backup{}.stats.json".format(filepath, backupsuffix)
            shutil.move(oldpath, newname)
            print("Moved {} to {} to avoid name collision".format(oldpath, newname), file=sys.stderr)
    args = args[0:5]

    with open(filepath, encoding="utf-8") as fd:
        try:
            kwags = dict(kwargs)
            kwags['fd_fp'] = filepath
            return evaluate(fd, *args, **kwags)
        except Exception as e:
            print("Error while processing {}".format(filepath), file=sys.stderr)
            raise e


def evaluate(fd, outfile, format=None, ignore_lines='c%', fullpath=False, hashes=True, fd_fp=""):
    """Evaluate cnfanalysis features for the CNF file provided
    in file descriptor `fd` and write features to filepath `outfile`.

    :param fd:              file descriptor to read from
    :type fd:               file descriptor
    :param outfile:         file path to write to
    :type outfile:          str
    :param format:          desired format of outfile: 'xml' or 'json'
    :type format:           str
    :param ignore_lines:    a string of prefixes of lines to ignore,
                            e.g. 'c' means ignore all lines starting with 'c'
    :type ignore_lines:     str
    :param fullpath:        shall I store the full path in JSON?
    :type fullpath:         bool
    :param hashes:          shall I compute hashes for this file?
    :type hashes:           bool
    :param fd_fp:           filepath of file descriptor
    :type fd_fp:            str
    """
    reader = dimacs.read(fd, ignore_lines)
    state = collect.State()
    header_fns = [collect.header_features]
    clause_fns = [collect.linear_clause_features, collect.type3_clause_features]
    literal_fns = [collect.linear_literal_features, collect.type3_literal_features]

    collect.dispatch(reader, state, header_fns, clause_fns, literal_fns)

    features = state.finalize()
    if format == 'json' or not format:
        stats.write_json(outfile, features, sourcefile=fd_fp, fullpath=fullpath, hashes=hashes)
    else:
        stats.write_xml(outfile, features, sourcefile=fd_fp, fullpath=fullpath, hashes=hashes)

    print('File {} has been written.'.format(outfile))

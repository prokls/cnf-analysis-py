#!/usr/bin/env python3

"""
    cnfanalysis.scripts
    -------------------

    Convenient functions for perform tasks with cnfanalysis.

    (C) 2015-2016, CC-0, Lukas Prokop
"""

import re
import sys
import json
import os.path
import argparse
import operator
import datetime
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
    parser.add_argument('-u', '--units', type=int, default=os.cpu_count() or 1,
                        help='how many units (= processes) should run in concurrently')
    parser.add_argument('-n', '--no-hashes', action='store_true',
                        help='do not compute hashes for the CNF file considered')
    parser.add_argument('-p', '--fullpath', action='store_true',
                        help='use full path instead of basename in featurefiles')
    parser.add_argument('-s', '--skip-existing', action='store_true',
                        help='skip CNF file if file.stats.json exists')

    # TODO: support gzipped files

    def derive_outfile(filepath, fmt):
        base, ext = filepath.rsplit('.', 1)
        if ext == 'gz':
            base, ext = base.rsplit('.', 1)
        return base + '.stats.' + fmt

    args = parser.parse_args()
    arguments = [args.format, ''.join(args.ignore or ['%', 'c']), args.fullpath,
                 not args.no_hashes, args.skip_existing]
    with multiprocessing.Pool(args.units) as p:
        p.starmap(evaluate_file, [[i, derive_outfile(i, args.format)] + arguments
                                  for i in args.dimacsfiles])


def annotate():
    desc = 'Annotate CNF feature files. Syntax for criteria: "<feature>{==,!=,>,<}<value>"'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-c', '--criterion', action='append',
                        help='criterion which has to be met')
    parser.add_argument('-t', '--tag', action='append',
                        help='tag to annotate, i.e. append to @tags')
    parser.add_argument('statsfiles', nargs='+',
                        help='feature files to annotate')

    args = parser.parse_args()

    def parse_criterion(crit):
        op = None
        for o in {'==', '!=', '>', '<'}:
            if o in crit:
                op = o
        if op is None:
            raise ValueError('No operator like {==,!=,>,<} found in criterion')
        feature, op, val = crit.split(op)
        if val.lower() in {'true', 'false'}:
            val = True if val.lower() == 'true' else False
        elif val.lower() == 'nan' or re.search(r'[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?', val):
            val = float(val)
        elif re.search(r'\d+', val):
            val = int(val)
        else:
            val = str(val)
        op = {'==': operator.eq, '!=': operator.ne, '>': operator.gt, '<': operator.lt}[op]
        print('Considering criterion: {}'.format((feature.strip(), op, val)), file=sys.stderr)
        return feature.strip(), op, val

    if not args.tag:
        raise ValueError('Expected at least one tag to be provided with "-t TAG"')

    if args.criterion:
        crits = [parse_criterion(c) for c in args.criterion]
    else:
        crits = []
    tags = ' '.join(args.tag)
    for statsfile in args.statsfiles:
        with open(statsfile) as fd:
            data = json.load(fd)
        for cnf in data:
            # check criteria
            met = True
            for (feature, op, value) in crits:
                if feature.startswith('@'):
                    if not op(cnf[feature], value):
                        met = False
                else:
                    if not op(cnf['featuring'][feature], value):
                        met = False
            if not met:
                continue
            # add tags
            if '@tags' not in cnf:
                cnf['@tags'] = tags
            else:
                cnf['@tags'] += ' ' + tags
        # write statsfile
        with open(statsfile, 'w') as fd:
            json.dump(data, fd, indent=2, sort_keys=True)
            print('Updated: {}'.format(statsfile), file=sys.stderr)


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
            warning = "Moved {} to {} to avoid name collision"
            print(warning.format(oldpath, newname), file=sys.stderr)
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
    print('{} - {} starting'.format(datetime.datetime.now().isoformat(), outfile))
    reader = dimacs.read(fd, ignore_lines)
    state = collect.State()
    header_fns = [collect.header_features]
    clause_fns = [collect.linear_clause_features, collect.expensive_clause_features]
    literal_fns = [collect.linear_literal_features, collect.expensive_literal_features]

    collect.dispatch(reader, state, header_fns, clause_fns, literal_fns)

    features = state.finalize()
    if format == 'json' or not format:
        stats.write_json(outfile, features, sourcefile=fd_fp, fullpath=fullpath, hashes=hashes)
    else:
        stats.write_xml(outfile, features, sourcefile=fd_fp, fullpath=fullpath, hashes=hashes)

    print('{} - {} written'.format(datetime.datetime.now().isoformat(), outfile))

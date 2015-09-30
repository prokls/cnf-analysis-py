#!/usr/bin/env python3

"""
    cnf-analysis-index
    ==================

    Directory index for CNF analysis.

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import re
import sys
import math
import os.path
import argparse
import multiprocessing
import subprocess

"""

        size                SHA-1                                   MD-5                                 cnfhash                           filename
      ------- ---------------------------------------- -------------------------------- ---------------------------------------- ---------------------------------

    directory .

      123.3KB a00c67c9375dbf80584cfc031719fc97fa925ab4 c60c9038289996b2403ce43be2d57540 a00c67c9375dbf80584cfc031719fc97fa925ab4 test.c


"""

def humanreadable_filesize(size: int) -> str:
    """Given integer of size in bytes, return human-readable representation"""
    order = int(math.log2(size))
    suf = ['', 'KiB', 'MiB', 'GiB', 'TiB', 'EiB', 'ZiB']
    return '{:.4g} {}'.format(size / (1 << (order)), suf[order // 10])


def grep_hashvalues(queries: [(str, str)]) -> str:
    """Grep for hash values """
    args_per_call = []
    for hashfile, path in queries:
        args_per_call.append(('grep', path, hashfile))

    with multiprocessing.Pool(processes=3) as pool:
        result = pool.map(subprocess.check_output, args_per_call).decode('utf-8')
        # TODO: CalledProcessError is raised if grep has found nothing




def header(sha1: bool, md5: bool, cnfhash: bool) -> str:
    """Create the header."""
    first_line = '  '
    first_line += 'size'.center(9)
    if sha1:
        first_line += ' '
        first_line += 'SHA-1'.center(40)
    if md5:
        first_line += ' '
        first_line += 'MD-5'.center(32)
    if cnfhash:
        first_line += ' '
        first_line += 'cnfhash'.center(40)
    first_line += ' '
    first_line += 'filename'.center(40)

    second_line = '  ' + '-' * 9
    if sha1:
        second_line += ' ' + ('-' * 40)
    if md5:
        second_line += ' ' + ('-' * 32)
    if cnfhash:
        second_line += ' ' + ('-' * 40)
    second_line += ' ' + ('-' * 40)

    return first_line + '\n' + second_line + '\n\n'



def main(args: argparse.Namespace) -> int:
    """Main routine."""
    def raise_error(e):
        raise e

    print(header(bool(args.sha1), bool(args.md5), bool(args.cnfhash)))

    for (dirpath, dirnames, filenames) in os.walk(args.directory, onerror=raise_error):
        print('directory {}\n\n'.format(dirpath))

        for filename in filenames:
            if os.path.splitext(filename)[1] != '.cnf':
                continue

            filepath = os.path.join(dirpath, filename)
            while filepath.startswith('./'):
                filepath = filepath[2:]

    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine CNF analysis results')

    parser.add_argument('directory', help='the directory to consider .cnf files in')
    parser.add_argument('--sha1', dest='sha1',
                        help='file containing sha1sum results for the files')
    parser.add_argument('--md5', dest='md5',
                        help='file containing sha1sum results for the files')
    parser.add_argument('--cnfhash', dest='cnfhash',
                        help='file containing sha1sum results for the files')

    args = parser.parse_args()
    sys.exit(main(args))

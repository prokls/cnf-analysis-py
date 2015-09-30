#!/usr/bin/env python3

"""
    cnf-analysis-inspect
    ====================

    Given a directory, I will tell you whether all .stats files exist
    or you missed something.

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import re
import sys
import hashlib
import os.path
import logging
import argparse

E_SYMB = 'Symbolic link detected. Not following {}'
E_EMPTY_DIR = 'Directory is empty. Suspicious! {}'
E_UNCOMPR_EQUAL = ('Uncompressed multiple times. '
                   'The following files are equivalent: {} = {}')
E_UNCOMPR_DIFF = 'Uncompressed multiple times. But files differ: {} != {}'
E_UNCOMPR_MULT_MISSING = ('The file name indicates that multiple '
                          'decompressions took place, but base file '
                          'does not exist: {}')
E_UNCOMPR_ARCHIVE = 'Uncompressed archive is still an archive: {} ⇒ {}'
E_UNCOMPR_MISSING = 'Cannot find decompressed folder (with same name): {}'
E_STATS_MISSING = 'cnf-analysis stats file not found for {}'
E_STATS_EMPTY = 'cnf-analysis stats file is empty: {}'


def is_empty_file(filepath: str) -> bool:
    """Is the file at given filepath empty?"""
    return os.stat(filepath).st_size == 0


def is_file_to_ignore(filepath: str) -> bool:
    """Shall I just ignore the given file?"""
    if os.path.basename(filepath) == '.DS_Store':
        return True
    if os.path.basename(filepath).startswith('README'):
        return True
    ignore_ext = {'.pdf', '.stats'}
    if os.path.splitext(filepath)[1] in ignore_ext:
        return True
    return False


def is_cnf_file(filepath: str) -> bool:
    if not filepath.endswith('.cnf'):
        return False
    if is_empty_file(filepath):
        raise IOError("Expected CNF file {} to be non-empty".format(filepath))
    return True


def is_archive(filepath: str) -> bool:
    """Does the file extension of the given filepath indicate an archive?"""
    fileextensions = {'.tgz', '.bz2', '.rar', '.zip', '.7z', '.tar', '.tar', '.gz', '.bzip', '.cab'}
    ext = os.path.splitext(filepath)[1]
    return ext in fileextensions


def files_are_equal(path1, path2) -> bool:
    """Check whether two files are equivalent using hashing algorithms"""
    def hash_file(filepath):
        sha1 = hashlib.sha1()
        f = open(filepath, 'rb')
        try:
            sha1.update(f.read())
        finally:
            f.close()
        return sha1.hexdigest()

    hash1 = hash_file(path1)
    hash2 = hash_file(path2)

    return hash1 == hash2


def main(args: argparse.Namespace, log: logging.Logger) -> int:
    """Main routine."""
    def raise_error(e):
        raise e

    for (dirpath, dirnames, filenames) in os.walk(args.directory, onerror=raise_error):
        for dirname in dirnames:
            folderpath = os.path.join(dirpath, dirname)
            if os.path.islink(folderpath):
                log.warn(E_SYMB.format(folderpath))
                continue
            if not os.listdir(folderpath):
                log.info(E_EMPTY_DIR.format(folderpath))

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if is_file_to_ignore(filepath):
                continue
            match = re.search(r' \(\d+\)$', filename)
            if match:
                base = filename[:match.span()[0]]
                basepath = os.path.join(dirpath, base)
                if os.path.exists(basepath):
                    if files_are_equal(basepath, filepath):
                        log.info(E_UNCOMPR_EQUAL.format(basepath, filepath))
                    else:
                        log.warn(E_UNCOMPR_DIFF.format(basepath, filepath))
                else:
                    log.warn(E_UNCOMPR_MULT_MISSING.format(filepath))
            if is_archive(filepath):
                base = os.path.splitext(filename)[0]
                if base.endswith('.tar'):  # .tar.gz
                    base = base[:-4]
                basepath = os.path.join(dirpath, base)
                if os.path.exists(basepath):
                    pass
                elif is_archive(basepath):
                    log.error(E_UNCOMPR_ARCHIVE.format(filepath, basepath))
                else:
                    log.error(E_UNCOMPR_MISSING.format(filepath))
            elif is_cnf_file(filepath):
                statsfile = os.path.join(dirpath, filename + ".stats")
                if not os.path.exists(statsfile):
                    log.error(E_STATS_MISSING.format(filepath))
                elif is_empty_file(statsfile):
                    log.error(E_STATS_EMPTY.format(filepath))
            else:
                log.error("Unknown file: {}".format(filepath))

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine CNF analysis results')
    parser.add_argument('directory', help='the directory to check')

    logging.basicConfig(level=logging.NOTSET, format='%(levelname) 8s - %(message)s')
    log = logging.getLogger('dirinfo')

    args = parser.parse_args()
    sys.exit(main(args, log))

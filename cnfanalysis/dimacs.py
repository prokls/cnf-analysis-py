#!/usr/bin/env python3

"""
    cnfanalysis.dimacs
    ------------------

    Library to handle DIMACS CNF files.

    (C) 2015-2016, CC-0, Lukas Prokop
"""

import re


class NbVarsError(ValueError):
    pass


class NbClausesError(ValueError):
    pass


def read(filedescriptor, ignore_lines='c%',
         check_nbvars=False, check_nbclauses=False):
    """Read nbvars, nbclauses and literals of a DIMACS CNF file.
    The file descriptor provided must return decoded str objects.
    `ignore_lines` cannot ignore header lines (i.e. 'p'-lines).
    This function ensures the final value is clause terminator zero
    after the last clause.

    Given a CNF file like::

        p cnf 4 3
        1 -2 0
        3 -4 -2 0
        c the last of 3 clauses
        1 -4 0

    return a generator yielding the following integers::

        [4, 3, 1, -2, 0, 3, -4, -2, 0, 1, -4, 0]

    :param filedescriptor:  file descriptor returning DIMACS CNF content
    :param ignore_lines:    prefixes of lines to ignore
                            (like 'c' for comment lines)
    :type ignore_lines:     [str]
    :return:                generator for header values and literals
    """
    mode = 0
    was_zero = False
    clauses = 0
    nbclauses = 0
    nbvars = 0

    for lineno, line in enumerate(filedescriptor):
        errsuf = " at line {}".format(lineno + 1)
        is_ignoreline = any(line.startswith(p) for p in ignore_lines)

        if line[0] == 'p':
            if mode != 0:
                msg = 'Unexpected DIMACS header' + errsuf
                raise ValueError(msg)
            else:
                header = re.match('p cnf\s+(\d+)\s+(\d+)\s*$', line, re.I)
                if not header:
                    raise ValueError('Invalid header line' + errsuf)
                nbvars = int(header.group(1))
                yield nbvars
                nbclauses = int(header.group(2))
                yield nbclauses
                mode = 1

        elif line.strip() == '' or is_ignoreline:
            pass

        else:
            if mode != 1:
                msg = 'Expected CNF header, got clause line' + errsuf
                raise ValueError(msg.format(lineno))

            vals = line.split()
            for lit in map(int, vals):
                was_zero = (lit == 0)
                if was_zero:
                    clauses += 1
                if check_nbvars and (-nbvars <= lit <= nbvars):
                    errmsg = 'Literal {} exceeds nbvars [-{}, {}]'
                    raise NbVarsError(errmsg.format(lit, -nbvars, nbvars))
                yield lit

    if mode == 0:
        raise ValueError('Empty DIMACS CNF file. Expected at least a header')
    if mode == 1 and not was_zero:
        yield 0
    if check_nbclauses and clauses != nbclauses:
        errmsg = 'Expected {} clauses, got {} clauses'
        raise NbClausesError(errmsg.format(nbclauses, clauses))

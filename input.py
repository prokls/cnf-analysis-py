#!/usr/bin/env python3

"""
    cnf-analysis.input
    ==================

    Read CNF files.

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import re
import _io

import processing


def read_dimacs(fp: _io.TextIOWrapper, analyzer: processing.Ipasir, *, ignoreheader=False):
    """Take a file descriptor and fill analyzer with data
    using the IPASIR interface. Returns None.
    """
    lineno, state = 1, 1 if ignoreheader else 0
    clause_regex = '^\s*((-?\d+)\s+)+?0\s*$'
    actually_interpreted = 0

    for line in fp:
        if line[0] == 'p':
            if not ignoreheader:
                msg = 'Unexpected DIMACS header at line {}'
                assert state == 0, msg.format(lineno)
                state = 1

                header = re.search('^p cnf\s+(\d+)\s+(\d+)\s+$', line, re.I)
                assert header, 'Invalid header line at line {}'.format(lineno)

                if getattr(analyzer, 'headerline'):
                    analyzer.headerline(int(header.group(1)), int(header.group(2)))

                actually_interpreted += 1

        elif line[0] == 'c' or line.strip() == '':
            pass

        else:
            msg = 'Clause lines must have layout {} at line {}'
            assert re.search(clause_regex, line), msg.format(clause_regex, lineno)

            msg = 'Expected header, unexpected clause at line {}'
            assert state == 1, msg.format(lineno)

            matches = re.findall('(-?\d+)(\s+|$)', line)
            if any(int(m[0]) == 0 for m in matches[:-1]):
                raise ValueError('Literal must not be 0 at line {}'.format(lineno))
            for match in matches:
                analyzer.add(int(match[0]))
            actually_interpreted += 1

        lineno += 1

    if actually_interpreted == 0:
        raise ValueError('Is not a DIMACS file')


def read_multiline_dimacs(fp: _io.TextIOWrapper, analyzer: processing.Ipasir, *, ignoreheader=False):
    """Take a file descriptor and fill analyzer with data
    using the IPASIR interface. Allows arbitrary newlines between literals.
    Returns None.
    """
    lineno, state = 0, 1 if ignoreheader else 0
    actually_interpreted = 0

    for line in fp:
        parts = line.split()
        lineno += 1

        if line[0] == 'c' or line.strip() == '':
            continue

        if state == 0 and not ignoreheader:
            msg = 'Invalid DIMACS header at line {}'
            assert parts[0].lower() == 'p', msg.format(lineno)

            msg = 'DIMACS header line should have value "cnf" as second element at line {}'
            assert parts[1].lower() == 'cnf', msg.format(lineno)

            msg = 'DIMACS header line should have 4 values at line {}'
            assert len(parts) == 4, msg.format(lineno)

            state = 1
            actually_interpreted += 1

            if getattr(analyzer, 'headerline'):
                analyzer.headerline(int(parts[2]), int(parts[3]))

            continue

        if parts[0] == 'p' and ignoreheader:
            continue

        # there are strange DIMACS implementations out there
        if len(parts) == 1 and parts[0] == '%':
            return

        msg = 'Expected header, unexpected clause at line {}'
        assert state == 1, msg.format(lineno)

        for part in parts:
            analyzer.add(int(part))

        actually_interpreted += 1

    if actually_interpreted == 0:
        raise ValueError('Is not a DIMACS file')

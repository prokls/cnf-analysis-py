#!/usr/bin/env python3

"""
    cnf-analysis
    ============

    Analyse files specifying a CNF.
    Supports
    - the DIMACS format
    - the IPASIR format [0]

    [0] http://baldur.iti.kit.edu/sat-race-2015/index.php?cat=rules#api

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import re
import sys
import json
import datetime
import statistics
import lxml.etree
import argparse
import collections

__version__ = '1.5.4'
__author__ = 'Lukas Prokop <lukas.prokop@student.tugraz.at>'

SAT = 10
UNSAT = 20


class Ipasir:
    """A class implementing the IPASIR interface."""

    def __init__(self):
        self.solver_state = 'INPUT'
        self.callback = None
        self.callback_arg = None

    def signature(self) -> str:
        return "IPASIR interface 1.1.0"

    def release(self) -> None:
        """Release the solver, i.e., all its resources and
        allocated memory (destructor). The solver pointer
        cannot be used for any purposes after this call.
        """
        assert self.solver_state in {'INPUT', 'SAT', 'UNSAT'}

        self.solver_state = 'undefined'

    def add(self, lit_or_zero: int) -> None:
        """Add the given literal into the currently added clause
        or finalize the clause with a 0. Clauses added this way
        cannot be removed. The addition of removable clauses
        can be simulated using activation literals and assumptions.

        Literals are encoded as (non-zero) integers as in the
        DIMACS formats.
        """
        assert self.solver_state in {'INPUT', 'SAT', 'UNSAT'}

        self.solver_state = 'INPUT'

    def assume(self, lit: int) -> None:
        """Add an assumption for the next SAT search (the next call
        of `solve`). After calling `solve` all the previously added
        assumptions are cleared.
        """
        assert self.solver_state in {'INPUT', 'SAT', 'UNSAT'}

        self.solver_state = 'INPUT'

    def solve(self) -> int:
        """Solve the formula with specified clauses under the
        specified assumptions.

        If the formula is satisfiable the function returns 10.
        If the formula is unsatisfiable the function returns 20.
        If the search is interrupted (see set_terminate)
        the function returns 0.
        """
        assert self.solver_state in {'INPUT', 'SAT', 'UNSAT'}

        self.solver_state = 'UNSAT'
        return UNSAT

    def val(self, lit: int) -> int:
        """Get the truth value of the given literal in the found satisfying
        assignment. Return 'lit' if True, '-lit' if False, and 0
        if it's not important. This function can only be used if `solve`
        has returned 10 and no `add` nor `assume` has been called since then.
        """
        assert self.solver_state == 'SAT'
        return 0

    def failed(self, lit: int) -> bool:
        """Check if the given assumption literal was used to prove the
        unsatisfiability of the formula under the assumptions
        used for the last SAT search. Return 1 if so, 0 otherwise.
        This function can only be used if `solve` has returned 20 and
        no `add` or `assume` has been called since then.
        """
        assert self.solver_state == 'UNSAT'
        return False

    def set_terminate(self, arg: object, terminate: type(lambda: 0)):
        """Set a callback function used to indicate a termination requirement to the
        solver. The solver will periodically call this function and check its return
        value during the search. The `set_terminate` function can be called in any
        state of the solver.
        The callback function is of the form "terminate(state) -> int"
          - it returns a non-zero value if the solver should terminate.
          - the solver calls the callback function with the parameter "state"
            having the value passed in the SetTerminate function (2nd parameter).

        Required state: INPUT or SAT or UNSAT
        State after: INPUT or SAT or UNSAT
        """
        assert self.solver_state in {'INPUT', 'SAT', 'UNSAT'}

        self.callback = terminate
        self.callback_arg = arg


class IpasirAnalyzer(Ipasir):
    def __init__(self, *, filepath='', time=''):
        super().__init__()
        self.active_clause = False
        self.clauses = set()
        self.literals = set()
        self.variables = set()
        self.clause = []
        self.metrics = {}

        self.clause_duplicates = 0
        self.literal_recurrence = collections.defaultdict(int)
        self.tautological_literals = 0
        self.tautological_clauses = 0

        if time:
            self.metrics['@time'] = str(time)
        else:
            self.metrics['@time'] = datetime.datetime.now().isoformat()
        if filepath:
            self.metrics['@path'] = filepath

    def signature(self) -> str:
        return "IPASIR analyzer " + __version__

    def headerline(self, nbvars: int, nbclauses: int):
        self.header = (nbvars, nbclauses)

    def start_clause(self):
        """Called whenever a new clause is about to be read"""
        pass

    def end_clause(self, new_clause: tuple([int])):
        """Called whenever a new clauses is about to be added"""
        for lit in new_clause:
            self.literal_recurrence[abs(lit)] += 1
            self.variables.add(abs(lit))
            self.literals.add(lit)

        tautological_literals = 0
        for i, j in zip(range(0, len(new_clause) - 1), range(1, len(new_clause))):
            if i == -j:
                tautological_literals += 1
        self.tautological_literals += tautological_literals
        if tautological_literals == len(new_clause) / 2:
            self.tautological_clauses += 1

    def add(self, lit_or_zero: int):
        super().add(lit_or_zero)

        if lit_or_zero == 0:
            new_clause = tuple(sorted(self.clause, key=lambda v: abs(v)))
            if new_clause in self.clauses:
                self.clause_duplicates += 1
            self.clauses.add(new_clause)
            self.clause = []
            self.end_clause(new_clause)
        else:
            if not self.active_clause:
                self.active_clause = True
                self.start_clause()
                self.clause.append(lit_or_zero)
            else:
                self.clause.append(lit_or_zero)

    def check_header(self):
        """Check validity of DIMACS header and optionally add attributes"""
        computed_header = (len(self.variables), len(self.clauses))

        if hasattr(self, 'header') and computed_header != self.header:
            valid_var_number = computed_header[0] == self.header[0]
            valid_clause_number = computed_header[1] == self.header[1]

            msg = 'Claimed number of variables is {}, but is {}'
            assert valid_var_number, msg.format(self.header[0], computed_header[0])

            msg = 'Claimed number of clauses is {}, but is {}'
            assert valid_clause_number, msg.format(self.header[1], computed_header[1])

    def existential_literals(self):
        """How many literals occur only either positive or negative?"""
        # 0=no stats, 1=only neg, 2=only pos, 3=mixed
        stats = collections.defaultdict(int)

        for c in self.clauses:
            for lit in c:
                var, pos = abs(lit), lit > 0
                if stats[var] == 0:
                    stats[var] = 1 + int(pos)
                elif (stats[var] == 1 and pos) or (stats[var] == 2 and not pos):
                    stats[var] = 3

        return {
            'ex': sum(int(v < 3) for v in stats.values()),
            'pos': sum(int(v == 2) for v in stats.values()),
            'neg': sum(int(v == 1) for v in stats.values())
        }

    def unique_pure_literals(self):
        """How many unique clauses contain only one literal?"""
        # 0=non-pure, 1=pure neg, 2=pure pos, 3=pure mixed
        stats = collections.defaultdict(int)
        contradiction_var = 0

        for c in self.clauses:
            if len(c) == 1:
                var, pos = abs(c[0]), c[0] > 0
                if stats[var] == 0:
                    stats[var] = 1 + int(pos)
                elif (stats[var] == 1 and pos) or (stats[var] == 2 and not pos):
                    stats[var] = 3
                    contradiction_var = var

        return {
            'pure': len(stats),
            'pos': sum(int(v == 2) for v in stats.values()),
            'neg': sum(int(v == 1) for v in stats.values()),
            'contradiction': contradiction_var
        }

    def release(self):
        super().release()
        self.check_header()

        clause_lengths = [len(c) for c in self.clauses]
        count_pos_literals = sum(sum(int(l > 0) for l in c) for c in self.clauses)

        rec = self.literal_recurrence.values()
        ex = self.existential_literals()
        pure = self.unique_pure_literals()

        self.metrics.update({
            'count_clauses': len(self.clauses),
            'count_unique_clauses': len(self.clauses) - self.clause_duplicates,
            'count_unique_literals': len(self.literals),
            'count_unique_variables': len(self.variables),
            'count_existential_literals': ex['ex'],
            'count_pure_literals': pure['pure'],
            'highest_variable': max(self.variables),
            'lowest_variable': min(self.variables),
            'clause_length_sum': sum(clause_lengths),
            'clause_length_mean': statistics.mean(clause_lengths),
            'clause_length_std': statistics.stdev(clause_lengths),
            'positive_literals_ratio': count_pos_literals / sum(clause_lengths),
            'literal_recurrence_percent': statistics.mean(rec) / len(self.clauses),
            'literal_recurrence_mean': statistics.mean(rec),
            'literal_recurrence_sd': statistics.stdev(rec)
        })

        if self.tautological_literals > 0:
            self.metrics['tautological_literals'] = self.tautological_literals
        if self.tautological_clauses > 0:
            self.metrics['tautological_clauses'] = self.tautological_clauses

        if ex['ex'] > 0:
            self.metrics['count_existential_literals_positive'] = ex['pos']
            self.metrics['count_existential_literals_negative'] = ex['neg']

        if pure['pure'] > 0:
            self.metrics['count_pure_literals_positive'] = pure['pos']
            self.metrics['count_pure_literals_positive'] = pure['neg']
            if pure['contradiction'] != 0:
                self.metrics['pure_literals_contradiction'] = pure['contradiction']


def readDimacs(fp, analyzer: Ipasir, *, ignoreheader=False):
    """Take a file pointer and fill analyzer
    with data using the IPASIR interface. Returns None.
    """
    lineno, state = 1, 1 if ignoreheader else 0
    clause_regex = '^((-?\d+)\s+)+?0\s+$'

    for line in fp:
        if line[0] == 'p':
            if not ignoreheader:
                msg = 'Unexpected DIMACS header at line {}'
                assert state == 0, msg.format(lineno)
                state = 1

                header = re.search('^p cnf\s+(\d+)\s+(\d+)\s+$', line)
                assert header, 'Invalid header line at line {}'.format(lineno)

                if getattr(analyzer, 'headerline'):
                    analyzer.headerline(int(header.group(1)), int(header.group(2)))

        elif line[0] == 'c' or line.strip() == '':
            pass

        else:
            msg = 'Clause lines must have layout {} at line {}'
            assert re.search(clause_regex, line), msg.format(clause_regex, lineno)

            msg = 'Expected header, unexpected clause at line {}'
            assert state == 1, msg.format(lineno)

            matches = re.findall('(-?\d+)\s+', line)
            if any(int(m) == 0 for m in matches[:-1]):
                raise ValueError('Literal must not be 0 at line {}'.format(lineno))
            for match in matches:
                analyzer.add(int(match))

        lineno += 1


xml_options = {
    'xml_declaration': True,
    'pretty_print': True,
    'encoding': 'utf-8'
}


def toXml(metrics: [dict]) -> bytes:
    """Take a list of metrics dictionary and return XML representation."""
    metrics_elem = lxml.etree.Element('metrics')

    for metric in metrics:
        file_elem = lxml.etree.Element('file')

        for key in metric.keys():
            if key.startswith('@'):
                file_elem.attrib[key[1:]] = metric[key]

        for name, value in metric.items():
            if name.startswith('@'):
                continue
            metric = lxml.etree.Element('metric')
            metric.attrib[name] = str(value)
            file_elem.append(metric)

        metrics_elem.append(file_elem)

    tree = lxml.etree.ElementTree(metrics_elem)
    return lxml.etree.tostring(tree, **xml_options)


def toJson(metrics: [dict]) -> bytes:
    """Take a metrics dictionary and return JSON representation."""
    return json.dumps({'metrics': metrics}, indent=2).encode('utf-8') + b'\n'


def main(args: argparse.Namespace) -> int:
    """Main routine"""
    dimacsfiles = filter(lambda v: v != '-', args.dimacsfiles)
    read_stdin = '-' in args.dimacsfiles or len(args.dimacsfiles) == 0
    analyzers = []

    if read_stdin:
        print('No DIMACS filepaths provided. Expecting DIMACS content at stdin …')
        analyzers.append(IpasirAnalyzer())
        readDimacs(sys.stdin, analyzers[-1], ignoreheader=args.ignore_header)

    for dimacsfile in dimacsfiles:
        analyzers.append(IpasirAnalyzer(filepath=dimacsfile))
        with open(dimacsfile) as fp:
            readDimacs(fp, analyzers[-1])

    for analyzer in analyzers:
        analyzer.solve()
        analyzer.release()

    if args.format == 'xml':
        output = toXml([a.metrics for a in analyzers])
    else:  # elif args.format == 'json':
        output = toJson([a.metrics for a in analyzers])

    if args.output:
        with open(args.output, 'wb') as fp:
            fp.write(output)
    else:
        print(output.decode('utf-8'))

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CNF analysis')

    parser.add_argument('dimacsfiles', metavar='dimacsfiles', nargs='*',
                        help='filepath of DIMACS file')
    parser.add_argument('-f', '--format', default='json',
                        help='output format (default: json)')
    parser.add_argument('-p', '--ignore-header', action='store_true',
                        help='do not check validity of header lines (default: false)')
    parser.add_argument('-o', '--output', default='',
                        help='write output to this filepath (default: stdout)')

    args = parser.parse_args()
    sys.exit(main(args))

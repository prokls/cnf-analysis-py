#!/usr/bin/env python3

"""
    cnfanalysis.processing
    ----------------------

    Analyse CNF structures.

    (C) 2015, BSD 3-clause licensed, Lukas Prokop
"""

import sys
import math
import os.path
import hashlib
import datetime
import statistics
import collections

import python_algorithms.basic.union_find

SAT = 10
UNSAT = 20


class Ipasir:
    """A class implementing the IPASIR interface [0].

    [0] http://baldur.iti.kit.edu/sat-race-2015/index.php?cat=rules#api
    """

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

    def set_terminate(self, arg: object, terminate: type(lambda: 0)) -> None:
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


class ExtendedIpasir(Ipasir):
    def __init__(self):
        self.header = (None, None)
        self.clause = []
        self.active_clause = False
        super().__init__()

    def assume(self, lit: int) -> None:
        raise NotImplementedError("Assumptions are not supported")

    def add(self, lit_or_zero: int) -> None:
        super().add(lit_or_zero)

        if lit_or_zero == 0:
            self.end_clause(self.clause)
            self.clause = []
            self.active_clause = False
        else:
            if not self.active_clause:
                self.active_clause = True
                self.start_clause()
            self.clause.append(lit_or_zero)

    def solve(self) -> int:
        assert not self.active_clause
        return super().solve()

    def release(self) -> None:
        assert not self.active_clause
        self.finish()
        super().release()

    # utility

    def check_header(self, expected_vars: int, expected_clauses: int):
        """Check validity of DIMACS header"""
        computed_header = (expected_vars, expected_clauses)

        if self.header[0] != None and computed_header != self.header:
            valid_var_number = computed_header[0] == self.header[0]
            valid_clause_number = computed_header[1] == self.header[1]

            msg = 'Claimed number of variables is {}, but is actually {}'
            assert valid_var_number, msg.format(self.header[0], computed_header[0])

            msg = 'Claimed number of clauses is {}, but is actually {}. Do duplicates exists?'
            assert valid_clause_number, msg.format(self.header[1], computed_header[1])

    # new hooks

    def headerline(self, nbvars: int, nbclauses: int):
        """Define the header line that was read"""
        self.header = (nbvars, nbclauses)

    def start_clause(self):
        """Called whenever a new clause is about to be read"""
        pass

    def end_clause(self, new_clause: tuple([int])):
        """Called whenever a new clauses is about to be added"""
        pass

    def finish(self):
        """Called whenever the file has been fully read"""
        pass


METRICS_DOCUMENTATION = '''\
Undocumented values might be lost in future (major or minor) releases.

Three meta attributes
=====================

time
  UTC timestamp when parsing: ISO 8601 combined date and time format
filename
  basename of filepath parsed (available only if input was not stdin)
sha1sum
  SHA1 sum of the original CNF file (available only if input was not stdin)

Clauses
=======

clauses_count
  Number of clauses in the original file
clauses_length_mean
  Mean value for the length of a clause (= number of literals in a clause)
clauses_length_largest
  Length of the longest clause (by number of literals)
clauses_length_sd
  Standard deviation for the length of clauses
clauses_length_smallest
  Length of the shortest clause (by number of literals)
clauses_length_uniform
  true if all clauses have the same length, false otherwise
clauses_unique_count
  How many clauses are unique?
  If this number differs from **clauses_count**, an error will be thrown beforehand
  because duplicate clauses exist and the CNF header gets checked. If ``--ignore-header``
  is enabled, no check will be done and this number might useful.
xor2_count
  If {a,b} and {-a,-b} occur as clauses, the counter will be incremented by one

Literals
========

literals_count
  Total number of literals
literals_existential_count
  How many literals occur only either positive or negative?
literals_existential_positive_count
  How many literals occur only with positive sign?
literals_existential_negative_count
  How many literals occur only with negative sign?
literals_positive_in_clauses_count
  How many clauses contain literals with positive sign?
literals_positive_in_clauses_largest
  What's the maximum number of literals with positive sign in any clause?
literals_positive_in_clauses_mean
  How many literals have a positive sign in average?
literals_positive_in_clauses_sd
  Standard deviation for the number of literals with positive sign
literals_positive_in_clauses_smallest
  What's the minimum number of literals with positive sign in any clause?
literals_positive_in_clauses_sum
  How many literals have a positive sign in total?
literals_positive_ratio
  What is the probability that a random literal has a positive sign?
literals_unit_unique_contradictory_variable
  Variable which occurs with clauses a and -a in CNF (only printed if some variable is actually contradictory)
literals_unit_unique_count
  How many unique clauses with only one literal exist?
literals_unit_unique_positive_count
  How many unique clauses with only one positive literal exist? (only printed if >0)
literals_unit_unique_negative_count
  How many unique clauses with only one negative literal exist? (only printed if >0)
literals_unique_count
  Number of literals that occur at least once

tautological_literals
  Number of times a variable occurs with positive *and* negative sign in a clause

Variables
=========

variables_largest
  The numerically largest variable identifier
variables_lowest
  The numerically smallest variable identifier
variables_unique_count
  The total number of variables
variables_recurrence_largest
  What's the maximum number of occurences of a variable?
variables_recurrence_percent
  What's the probability that a random variable will occur in a random clause?
  Hence the number of occurences of a variable divided by the total number of clauses
variables_recurrence_sd
  Standard deviation for the number of occurences of a random variable
variables_recurrence_mean
  Mean value for the number of occurences of a random variable
variables_recurrence_smallest
  Minimum number of occurences of a variable
'''

METRICS = {
    'clauses_count' : (True,),
    'clauses_length_mean' : (True,),
    'clauses_length_largest' : (True,),
    'clauses_length_sd' : (True,),
    'clauses_length_smallest' : (True,),
    'clauses_unique_count' : (True,),
    'clause_uniform_length' : (True,),
    'literals_count' : (True,),
    'literals_existential_count' : (True,),
    'literals_existential_positive_count' : (False,),
    'literals_existential_negative_count' : (False,),
    'literals_positive_in_clauses_count' : (True,),
    'literals_positive_in_clauses_largest' : (True,),
    'literals_positive_in_clauses_mean' : (True,),
    'literals_positive_in_clauses_sd' : (True,),
    'literals_positive_in_clauses_smallest' : (True,),
    'literals_positive_in_clauses_sum' : (True,),
    'literals_positive_ratio' : (True,),
    'literals_unit_unique_contradictory_variable' : (False,),
    'literals_unit_unique_count' : (True,),
    'literals_unit_unique_positive_count' : (False,),
    'literals_unit_unique_negative_count' : (False,),
    'literals_unique_count' : (True,),
    'tautological_literals' : (False,),
    'tautological_clauses' : (False,),
    'variables_largest' : (True,),
    'variables_lowest' : (True,),
    'variables_unique_count' : (True,),
    'variables_recurrence_largest' : (True,),
    'variables_recurrence_percent' : (True,),
    'variables_recurrence_sd' : (True,),
    'variables_recurrence_mean' : (True,),
    'variables_recurrence_smallest' : (True,)
}

class IpasirAnalyzer(ExtendedIpasir):
    def __init__(self, writer, *, full_var_occurence=False, filepath='', time=''):
        super().__init__()
        self.clauses = set()
        self.literals = set()
        self.variables = set()
        self.full_var_occurence = full_var_occurence
        if full_var_occurence:
            self.var_occurence = collections.defaultdict(int)

        self.clause_duplicates = 0
        self.variable_recurrence = collections.defaultdict(int)
        self.tautological_literals = 0
        self.tautological_clauses = 0
        self.reference_length = -1
        self.uniform_length = True
        self.xor2 = set()
        self.xor2_count = 0
        self.comp = None

        self.clause = []
        self.writer = writer

        self.meta = {}

        if time:
            self.meta['@time'] = str(time)
        else:
            self.meta['@time'] = datetime.datetime.utcnow().isoformat()
        if filepath:
            self.meta['@filename'] = os.path.basename(filepath)
            try:
                md5 = hashlib.md5()
                sha1 = hashlib.sha1()

                with open(filepath, 'rb') as fp:
                    while True:
                        chunk = fp.read(65536)
                        if not chunk:
                            break
                        md5.update(chunk)
                        sha1.update(chunk)

                self.meta['@md5sum'] = md5.hexdigest()
                self.meta['@sha1sum'] = sha1.hexdigest()
            except FileNotFoundError:
                pass

    def signature(self) -> str:
        return "IPASIR analyzer 2.0.0"

    # statistics

    def integer_list_stats(self, lst, prefix, *, unique_count=None):
        """Provide statistics about a list of integers"""
        assert len(lst) > 0

        if len(lst) <= 2:
            mean = sum(lst) / len(lst)
            stdev = math.sqrt((1.0 / len(lst)) * sum([(v - mean)**2 for v in lst]))
        else:
            mean = statistics.mean(lst)
            stdev = statistics.stdev(lst)

        self.metrics[prefix + '_mean'] = mean
        self.metrics[prefix + '_sd'] = stdev
        self.metrics[prefix + '_sum'] = sum(lst)
        self.metrics[prefix + '_count'] = len(lst)
        self.metrics[prefix + '_smallest'] = min(lst)
        self.metrics[prefix + '_largest'] = max(lst)

        if unique_count is not None:
            self.writer.receive(prefix + '_unique_count', unique_count)

    # utilities

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

    def unique_unit_literals(self):
        """How many unique clauses contain only one literal?"""
        # 0=non-unit, 1=unit neg, 2=unit pos, 3=unit mixed
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
            'unit': len(stats),
            'pos': sum(int(v == 2) for v in stats.values()),
            'neg': sum(int(v == 1) for v in stats.values()),
            'contradiction': contradiction_var
        }

    # member updates

    def headerline(self, nbvars: int, nbclauses: int):
        """Storing header values"""
        self.comp = python_algorithms.basic.union_find.UF(nbvars + 1)
        return super().headerline(nbvars, nbclauses)

    def end_clause(self, new_clause: tuple([int])):
        """Add a clause and some statistics about it"""
        new_clause = tuple(sorted(new_clause, key=lambda v: abs(v)))
        super().end_clause(new_clause)

        if new_clause in self.clauses:
            print('Warning: Clause duplicate: {}'.format(new_clause), file=sys.stderr)
            self.clause_duplicates += 1
        else:
            self.clauses.add(new_clause)

        for lit in new_clause:
            self.variable_recurrence[abs(lit)] += 1
            self.variables.add(abs(lit))
            self.literals.add(lit)

        if len(new_clause) > 1 and self.comp:
            for i in range(1, len(new_clause)):
                self.comp.union(new_clause[0], new_clause[i])

        tautological_literals = 0
        for i, j in zip(range(0, len(new_clause) - 1), range(1, len(new_clause))):
            if new_clause[i] == -new_clause[j]:
                tautological_literals += 1
        self.tautological_literals += tautological_literals

        if tautological_literals == len(new_clause) / 2:
            self.tautological_clauses += 1

        if self.reference_length < 0:
            self.reference_length = len(new_clause)
        else:
            if self.reference_length != len(new_clause):
                self.uniform_length = False

        if self.full_var_occurence:
            self.var_occurence[abs(lit)] += 1

        if len(new_clause) == 2:
            pair = tuple(sorted(new_clause))
            if pair in self.xor2:
                self.xor2_count += 1
                self.xor2.remove(pair)
            else:
                self.xor2.add((-pair[1], -pair[0]))

    # finalization

    def finish(self):
        super().finish()
        self.check_header(len(self.variables), len(self.clauses) + self.clause_duplicates)
        self.metrics = {}

        # (1) number of [unique] clauses
        len_clauses = len(self.clauses) + self.clause_duplicates
        self.metrics['clauses_count'] = len_clauses
        self.metrics['clauses_unique_count'] = len(self.clauses)

        # (2) number of unique literals
        len_literals = len(self.literals)
        self.metrics['literals_unique_count'] = len_literals

        # (3) number of unique variables
        len_variables = len(self.variables)
        self.metrics['variables_unique_count'] = len_variables

        # (4) statistics for clauses
        clause_lengths = [len(c) for c in self.clauses]
        self.integer_list_stats(clause_lengths, 'clauses_length')

        # (5) statistics for literals
        pos_literals = [sum(int(l > 0) for l in c) for c in self.clauses]
        self.metrics['literals_count'] = sum(clause_lengths)
        self.integer_list_stats(pos_literals, 'literals_positive_in_clauses')
        self.metrics['literals_positive_ratio'] = sum(pos_literals) / sum(clause_lengths)

        # (6) statistics for variables
        self.metrics['variables_largest'] = max(self.variables)
        self.metrics['variables_lowest'] = min(self.variables)


        # (7) special: variable recurrence
        rec = self.variable_recurrence.values()
        self.integer_list_stats(list(rec), 'variables_recurrence')
        self.metrics['variables_recurrence_percent'] = statistics.mean(rec) / len_clauses

        # (8) special: existential literals
        ex = self.existential_literals()
        self.metrics['literals_existential_count'] = ex['ex']
        if ex['pos'] > 0:
            self.metrics['literals_existential_positive_count'] = ex['pos']
        if ex['neg'] > 0:
            self.metrics['literals_existential_negative_count'] = ex['neg']

        # (9) special: unique unit literals
        unit = self.unique_unit_literals()
        self.metrics['literals_unit_unique_count'] = unit['unit']
        if unit['pos'] > 0:
            self.metrics['literals_unit_unique_positive_count'] = unit['pos']
        if unit['neg'] > 0:
            self.metrics['literals_unit_unique_negative_count'] = unit['neg']
        if unit['contradiction'] > 0:
            self.metrics['literals_unit_unique_contradictory_variable'] = unit['contradiction']

        # (10) special: tautologies
        if self.tautological_literals > 0:
            self.metrics['tautological_literals'] = self.tautological_literals
        if self.tautological_clauses > 0:
            self.metrics['tautological_clauses'] = self.tautological_clauses

        # (11) special: connected components
        if self.comp and self.comp.count() > 0:
            self.metrics['connected_components'] = self.comp.count()

        # (12) special: xor2 detection
        if self.xor2_count > 0:
            self.metrics['xor2_count'] = self.xor2_count

        # (13) special: uniform clause length as used in lingeling for YalSAT
        self.metrics['clauses_length_uniform'] = self.uniform_length

        # (14) special: full variable occurence
        if self.full_var_occurence:
            stats = collections.defaultdict(int)
            invalid = False
            for var, count in self.var_occurence.items():
                if count > len_clauses:
                    invalid = True
                    break
                percent = (100 * count) // len_clauses
                stats[percent] += 1
            for k, count in stats.items():
                if invalid or count <= 0:
                    continue
                self.metrics['variables_occurence_ratio_{}'.format(k)] = count

        self.writer.write(self.meta, self.metrics)
        self.writer.finish()

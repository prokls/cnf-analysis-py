#!/usr/bin/env python3

"""
    cnfanalysis.collect
    -------------------

    Collect features of DIMACS CNF files.

    (C) 2015-2016, CC-0, Lukas Prokop
"""

import math
import statistics
import collections
import python_algorithms.basic.union_find


class State:
    def __init__(self):
        self.nbvars = 0
        self.nbclauses = 0
        self.clauses_count = 0
        self.literals_count = 0
        self.literals = set()
        self.clause_lengths = []
        self.positive_literals_in_clause = []
        self.negative_literals_in_clause = []
        self.literals_occurences = collections.defaultdict(int)
        self.clause_variables_sd = []
        self.positive_unit_clause_count = 0
        self.negative_unit_clause_count = 0
        self.two_literals_clause_count = 0
        self.tautological_literals_count = 0
        self.connected_literal_components_count = 0
        self.connected_variable_components_count = 0
        self.true_trivial = True
        self.false_trivial = True
        self.xor2_detect = collections.defaultdict(int)
        self.definite_clause_count = 0
        self.goal_clause_count = 0


    def finalize(self):
        """After dispatching the last literal, return a dictionary of
        features with their values.

        :return:        A dictionary associating feature name to its value
        :rtype:         dict
        """
        # TODO: support full_var_occurence
        variables_used = set(map(abs, self.literals))
        existential_lits, existential_pos_lits = 0, 0
        literals_occurence_one_count = 0
        for lit, freq in self.literals_occurences.items():
            if freq == 1:
                literals_occurence_one_count += 1
            if freq == 1 and self.literals_occurences.get(-lit, 0) == 0:
                existential_lits += 1
                if lit > 0:
                    existential_pos_lits += 1

        assert len(self.positive_literals_in_clause) == len(self.negative_literals_in_clause)
        pnlicre = 0.0
        pnlicrm = []
        for pos, neg in zip(self.positive_literals_in_clause, self.negative_literals_in_clause):
            # 0% = none is positive      100% = all are positive
            ratio = 1.0 * pos / (pos + neg)
            if ratio != 0.0:
                pnlicre += ratio * math.log(ratio, 2)
            pnlicrm.append(ratio)
        pnlicrm = statistics.mean(pnlicrm)

        # Assumption: number of clauses with literal X ~ number of occurences of X
        lit_freq, lit_freq_valid = [], True
        var_freq, var_freq_valid = [], True
        lit_freq_cat = [0] * 20
        var_freq_cat = [0] * 20
        for lit in range(-max(variables_used), max(variables_used) + 1):
            if lit == 0:
                continue
            freq = 1.0 * self.literals_occurences[lit] / self.nbclauses
            if freq > 1.0:
                lit_freq_valid = False
            lit_freq.append(freq)
            lit_freq_cat[int((100 * freq) // 5) if freq < 1.0 else 19] += 1
        for var in range(1, max(variables_used) + 1):
            freq = 1.0 * (self.literals_occurences[var] + self.literals_occurences[-var]) / self.nbclauses
            if freq > 1.0:
                var_freq_valid = False
            var_freq.append(freq)
            var_freq_cat[int((100 * freq) // 5) if freq < 1.0 else 19] += 1


        features = {
            'nbvars': self.nbvars,
            'nbclauses': self.nbclauses,
            'clauses_count': self.clauses_count,
            'literals_count': self.literals_count,
            'variables_used_count': len(variables_used),
            'variables_largest': max(variables_used),
            'variables_smallest': min(variables_used),
#            'clauses_unique_count': ,  # TODO
            'positive_literals_count': sum(self.positive_literals_in_clause),
            'positive_negative_literals_in_clause_ratio_entropy': -pnlicre,
            'positive_negative_literals_in_clause_ratio_mean': pnlicrm,
            'existential_literals_count': existential_lits,
            'existential_positive_literals_count': existential_pos_lits,
            'clause_variables_sd_mean': statistics.mean(self.clause_variables_sd),
            'positive_unit_clause_count': self.positive_unit_clause_count,
            'negative_unit_clause_count': self.negative_unit_clause_count,
            'two_literals_clause_count': self.two_literals_clause_count,
            'tautological_literals_count': self.tautological_literals_count,
            # Remark: count - 1, because "0" will not be connected to anyone
            'connected_literal_components_count': self.connected_literal_components.count() - 1,
            'connected_variable_components_count': self.connected_variable_components.count() - 1,
            'true_trivial': self.true_trivial,
            'false_trivial': self.false_trivial,
            'literals_occurence_one_count': literals_occurence_one_count,
#            'xor2_detect': , # TODO
            'definite_clauses_count': self.definite_clause_count,
            'goal_clauses_count': self.goal_clause_count
        }
        features.update(self._stat(self.clause_lengths, 'clauses_length', 'aimsd'))
        features.update(self._stat(self.positive_literals_in_clause, 'positive_literals_in_clause', 'aimsd'))
        features.update(self._stat(self.negative_literals_in_clause, 'negative_literals_in_clause', 'aim'))
        if lit_freq_valid:
            features.update(self._stat(lit_freq, 'literals_frequency', 'aimsde'))
        if var_freq_valid:
            features.update(self._stat(var_freq, 'variables_frequency', 'aimsde'))
        for begin, end in zip(range(0, 100, 5), range(5, 105, 5)):
            if lit_freq_valid and lit_freq_cat[begin // 5] != 0.0:
                features['literals_frequency_{}_to_{}'.format(begin, end)] = lit_freq_cat[begin // 5]
            if var_freq_valid and var_freq_cat[begin // 5] != 0.0:
                features['variables_frequency_{}_to_{}'.format(begin, end)] = var_freq_cat[begin // 5]

        return features

    @staticmethod
    def _stat(ints, prefix, spec='aimsd'):
        if not ints:
            return {}

        d = {}
        if 'a' in spec:
            d[prefix + '_largest'] = max(ints)
        if 'i' in spec:
            d[prefix + '_smallest'] = min(ints)
        if 'm' in spec:
            d[prefix + '_mean'] = statistics.mean(ints)
        if 's' in spec:
            d[prefix + '_sd'] = statistics.pstdev(ints)
        if 'd' in spec:
            d[prefix + '_median'] = statistics.median(ints)
        if 'e' in spec:
            d[prefix + '_entropy'] = 0.0
            for val in ints:
                if val <= 0.0:
                    continue
                d[prefix + '_entropy'] += val * math.log(val, 2)
            d[prefix + '_entropy'] = -d[prefix + '_entropy']
        return d


def header_features(state, nbvars, nbclauses):
    state.nbvars = nbvars
    state.nbclauses = nbclauses

    state.connected_literal_components = python_algorithms.basic.union_find.UF(2 * nbvars + 1)
    state.connected_variable_components = python_algorithms.basic.union_find.UF(nbvars + 1)


_poseq = lambda n: -2*n if n < 0 else 2*n - 1
def linear_clause_features(state, clause):
    """Linear computable clause features"""
    state.clauses_count += 1
    if state.clauses_count > state.nbclauses:
        raise ValueError("Expected {} clauses, but got more".format(state.nbclauses))
    if len(clause) == 1 and clause[0] > 0:
        state.positive_unit_clause_count += 1
    if len(clause) == 1 and clause[0] < 0:
        state.negative_unit_clause_count += 1
    if len(clause) == 2:
        state.two_literals_clause_count += 1

    taut = 0
    for lit in clause:
        if -lit in clause:
            taut += 1
    assert taut % 2 == 0
    state.tautological_literals_count += taut // 2

    for lit in clause[1:]:
        state.connected_literal_components.union(_poseq(clause[0]), _poseq(lit))
        state.connected_variable_components.union(abs(clause[0]), abs(lit))

    pos = len(list(filter(lambda v: v > 0, clause)))
    neg = len(list(filter(lambda v: v < 0, clause)))
    if neg == 0:
        state.false_trivial = False
    if pos == 0:
        state.true_trivial = False
    if pos == 1:
        state.definite_clause_count += 1
    if pos == 0:
        state.goal_clause_count += 1


def linear_literal_features(state, literal):
    """Linear computable literal features"""
    state.literals_count += 1

    if literal < -state.nbvars or literal > state.nbvars:
        errmsg = "Literal {} not in [-{}, {}] derived from nbvars"
        raise ValueError(errmsg.format(literal, state.nbvars, state.nbvars))


def type3_clause_features(state, clause):
    """Type 3 clause features"""
    state.clause_lengths.append(len(clause))
    pos = len(list(filter(lambda v: v > 0, clause)))
    state.positive_literals_in_clause.append(pos)
    state.negative_literals_in_clause.append(len(clause) - pos)

    sd = statistics.pstdev(map(abs, clause))
    state.clause_variables_sd.append(sd)

    if len(clause) == 2:
        s = sorted(clause)
        ref = (abs(s[0]), abs(s[1]))
        id = {True: 8, False: 4}[s[0] > 0] + {True: 2, False: 1}[s[1] > 0]
        state.xor2_detect[ref] |= id


def type3_literal_features(state, literal):
    """Type 3 literal features"""
    state.literals.add(literal)
    state.literals_occurences[literal] += 1


def dispatch(reader, state, header_update_fns, clause_update_fns, lit_update_fns):
    """Read literals from `reader` and dispatch to call corresponding functions.
    All `header_update_fns` will be called with `state` and the first two values of `reader`.
    If a clause was terminated, call all `clause_update_fns` with ``(state, clause)``.
    If a literal was read, call all `lit_update_fns` with ``(state, lit)``.

    :param reader:              An iterable for literals
    :type reader:               iter
    :param state:               any object to hold intermediate feature values
    :type state:                object
    :param header_update_fns:   Callables updating feature values for header values
    :type header_update_fns:    Callable
    :param clause_update_fns:   Callables updating feature values for a given clause
    :type clause_update_fns:    Callable
    :param lit_update_fns:      Callables updating feature values for a given literal
    :type lit_update_fns:       Callable
    """
    # DIMACS CNF header
    nbvars = next(reader)
    nbclauses = next(reader)
    for fn in header_update_fns:
        fn(state, nbvars, nbclauses)

    # clauses and literals
    clause = []
    for lit in reader:
        if lit == 0:
            for fn in clause_update_fns:
                fn(state, tuple(clause))
            clause = []
        else:
            for fn in lit_update_fns:
                fn(state, lit)
            clause.append(lit)

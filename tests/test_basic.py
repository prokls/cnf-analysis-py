#!/usr/bin/env python3

import io
import json
import unittest

import cnfanalysis.scripts
import cnfanalysis.statsfile
import cnfanalysis.dimacsfile
import cnfanalysis.processing


class TestCnfAnalysis(unittest.TestCase):
    @staticmethod
    def run_for_clauses(clauses, nbvars):
        # write clauses to pseudo-file
        inp = io.StringIO()
        inp.write('p cnf {} {}\n'.format(nbvars, len(clauses)))
        for clause in clauses:
            for lit in clause:
                inp.write(str(lit) + ' ')
            inp.write('0\n')
        inp.seek(0)

        # ask to read file
        out = io.BytesIO()
        writer = cnfanalysis.statsfile.Writer(out, format='json', encoding='ascii')
        analyzer = cnfanalysis.processing.IpasirAnalyzer(writer)
        cnfanalysis.dimacsfile.read(inp, analyzer)

        # generate metrics
        analyzer.solve()
        analyzer.release()
        out.seek(0)

        # return result
        data = json.loads(out.read().decode('ascii'))
        return data


    def test_simple(self):
        metrics = self.run_for_clauses([[1,2,3]], 3)
        expect = {
            'clauses_count': 1,
            'clauses_length_count': 1,
            'clauses_length_largest': 3,
            'clauses_length_mean': 3.0,
            'clauses_length_sd': 0.0,
            'clauses_length_smallest': 3,
            'clauses_length_sum': 3,
            'clauses_unique_count': 1,
            'connected_components': 2,
            'literals_count': 3,
            'literals_existential_count': 3,
            'literals_existential_positive_count': 3,
            'literals_positive_in_clauses_count': 1,
            'literals_positive_in_clauses_largest': 3,
            'literals_positive_in_clauses_mean': 3.0,
            'literals_positive_in_clauses_sd': 0.0,
            'literals_positive_in_clauses_smallest': 3,
            'literals_positive_in_clauses_sum': 3,
            'literals_positive_ratio': 1.0,
            'literals_unique_count': 3,
            'literals_unit_unique_count': 0,
            'variables_largest': 3,
            'variables_lowest': 1,
            'variables_recurrence_count': 3,
            'variables_recurrence_largest': 1,
            'variables_recurrence_mean': 1.0,
            'variables_recurrence_percent': 1.0,
            'variables_recurrence_sd': 0.0,
            'variables_recurrence_smallest': 1,
            'variables_recurrence_sum': 3,
            'variables_unique_count': 3
        }

        for k, v in metrics['metrics'][0]['metric'].items():
            self.assertEqual(v, expect[k])

if __name__ == '__main__':
    unittest.main()

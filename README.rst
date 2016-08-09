cnf-analysis
============

:author:     Lukas Prokop
:date:       June 2015 to August 2016
:version:    1.0.0
:license:    CC-0

cnf-analysis is a library to analyze DIMACS CNF files.
Those files are commonly used to decode SAT problems and
a few basic features of a CNF file might tell you something
about the problem stated.

This tool evaluates a list of features which are thoroughly
described by the project and stores them in a JSON file.

How To Use
----------

To install use pip3::

    $ pip3 install cnfanalysis

Then the command line tool to analyze CNF files is available::

    $ echo "p cnf 3 2\n1 -3 0\n2 3 -1 0\n" > example.cnf
    $ cnf-analysis-py example.cnf
    File example.stats.json has been written.
    $ cat example.stats.json
    [
      {
        "@cnfhash": "cnf2$7d16f8d71b7097a2f931936ae6d03d738117b2c6",
        "@filename": "example.cnf",
        "@md5sum": "04f6bf2c537242f15082867e66847bd7",
        "@sha1sum": "23dd9e64ae0fb4806661b49a31e7f5e692f2d045",
        "@timestamp": "2016-08-03T10:52:23.412694",
        "@version": "1.0.0",
        "featuring": {
          "clause_variables_sd_mean": 0.908248290463863,
          "clauses_count": 2,
          "clauses_length_largest": 3,
          "clauses_length_mean": 2.5,
          "clauses_length_median": 2.5,
          "clauses_length_sd": 0.5,
          "clauses_length_smallest": 2,
          "connected_literal_components_count": 3,
          "connected_variable_components_count": 1,
          "definite_clauses_count": 1,
          "existential_literals_count": 1,
          "existential_positive_literals_count": 1,
          "false_trivial": true,
          "goal_clauses_count": 0,
          "literals_count": 5,
          "literals_frequency_0_to_5": 1,
          "literals_frequency_50_to_55": 5,
          "literals_frequency_entropy": 2.5,
          "literals_frequency_largest": 0.5,
          "literals_frequency_mean": 0.4166666666666667,
          "literals_frequency_median": 0.5,
          "literals_frequency_sd": 0.18633899812498247,
          "literals_frequency_smallest": 0.0,
          "literals_occurence_one_count": 5,
          "nbclauses": 2,
          "nbvars": 3,
          "negative_literals_in_clause_largest": 1,
          "negative_literals_in_clause_mean": 1,
          "negative_literals_in_clause_smallest": 1,
          "negative_unit_clause_count": 0,
          "positive_literals_count": 3,
          "positive_literals_in_clause_largest": 2,
          "positive_literals_in_clause_mean": 1.5,
          "positive_literals_in_clause_median": 1.5,
          "positive_literals_in_clause_sd": 0.5,
          "positive_literals_in_clause_smallest": 1,
          "positive_negative_literals_in_clause_ratio_entropy": 0.8899750004807708,
          "positive_negative_literals_in_clause_ratio_mean": 0.5833333333333333,
          "positive_unit_clause_count": 0,
          "tautological_literals_count": 0,
          "true_trivial": true,
          "two_literals_clause_count": 1,
          "variables_frequency_50_to_55": 1,
          "variables_frequency_95_to_100": 2,
          "variables_frequency_entropy": 0.5,
          "variables_frequency_largest": 1.0,
          "variables_frequency_mean": 0.8333333333333334,
          "variables_frequency_median": 1.0,
          "variables_frequency_sd": 0.23570226039551584,
          "variables_frequency_smallest": 0.5,
          "variables_largest": 3,
          "variables_smallest": 1,
          "variables_used_count": 3
        }
      }
    ]


Performance
-----------

``cnf-analysis-py`` puts CNF files supplied as command
line arguments into a process pool and uses processes
in the number of CPUs available on your machine.

This sort of parallelism should be best suited for python
and I retrieved the following runtime results (for SAT
competition 2016 CNF files):

* 3434 files (5.9 GB in total) in *Agile* took 23h 19min
* ``esawn_uw3.debugged.cnf`` (1.4 GB) in *app16* took 8 hours and 15 minutes
* ``bench_573.smt2.cnf`` (1.6 MB) in *Agile* took 2min 14sec

Be aware that the performance mainly depends on the features computed.
Designated tool to compute a subset of features can be much faster.

I am using my Thinkpad x220t with 16GB RAM and an Intel Core
i5-2520M CPU (2.50GHz) as reference system here.

Memory
------

Again, we consider SAT competition 2016 CNF files and besides Thinkpad x220t
we also consider a desktop system with an Intel Core i7 CPU (2.8GHz) but only
4 GB RAM.

In *Agile* CNF files have 1.7 MB average file size.
5 MB files take at most 50 MB (factor 10) to evaluate them.

``sin.c.75.smt2-cvc4.cnf`` (770 MB) in *app16* even yielded a MemoryError
in python on my Linux machine with only 4 GB. On my 16 GB machine it took
3 hours and 15 minutes.

``esawn_uw3.debugged.cnf`` used 8 GB RAM.


Certainly this implementation is not very memory efficient,
but also for large files, you should not run out of memory.

Dependencies
------------

* `python3 <http://python.org/>`_

It works with Python 3.4 or later. I tested it on linux x86_64.
Package dependencies are listed in ``requirements.txt``.


Command line options
--------------------

``-f xml``
  Use XML output instead of JSON
``--ignore c``
  Ignore any lines starting with "c"
``--no-hashes``
  skip hash computations
``--fullpath``
  print full path, not basename

DIMACS files
------------

DIMACS files are read by skipping any lines starting with characters
from ``--ignore``. The remaining content is parsed (header line with
``nbvars`` and ``nbclauses``) and in the remaining line, integers are
retrieved and passed over. Hence the parser yields a sequence of
literals.

Features
--------

TODO


Cheers,
prokls

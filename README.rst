cnf-analysis
============

cnf-analysis is a command line tool to analyse CNF files.
CNF files are expected to be written in DIMACS format.
After parsing them, they are read through an IPASIR interface.
On calling the release method, metrics about the CNF file are computed.

Dependencies
------------

* `python3 <http://python.org/>`_

I think it should work with every 3.x release.
However I tested it with Python 3.4.0 on linux x86_64.

Example
-------

Here you can see a simple example::

    $ python3 analysis.py satcomp2014_benchmarks/sc14-app/001-80-12.cnf

    {
      "metrics": [
        {
          "count_pure_literals_positive": 147,
          "count_unique_literals": 26816,
          "@time": "2015-06-21T22:55:46.358903",
          "clause_length_mean": 6.5592449549413985,
          "literal_recurrence_mean": 234.07816229116946,
          "count_clauses": 478488,
          "@path": "satcomp2014_benchmarks/sc14-app/001-80-12.cnf",
          "clause_length_sum": 3138520,
          "count_unique_clauses": 478488,
          "clause_length_std": 1.3266195149505624,
          "literal_recurrence_sd": 247.31242553401754,
          "count_pure_literals": 300,
          "count_existential_literals": 0,
          "literal_recurrence_percent": 0.0004892038301716437,
          "positive_literals_ratio": 0.502639142015982,
          "lowest_variable": 1,
          "count_unique_variables": 13408,
          "highest_variable": 13408
        }
      ]
    }

    python3 analysis.py   30.37s user 0.29s system 83% cpu 36.649 total

You can use ``--help`` to get help for the command-line tool::

    usage: analysis.py [-h] [-f FORMAT] [-p] [-o OUTPUT]
                       dimacsfiles [dimacsfiles ...]

    CNF analysis

    positional arguments:
      dimacsfiles           filepath of DIMACS file

    optional arguments:
      -h, --help            show this help message and exit
      -f FORMAT, --format FORMAT
                            output format (default: json)
      -p, --ignore-header   do not check validity of header lines (default: false)
      -o OUTPUT, --output OUTPUT
                            write output to this filepath (default: stdout)

Features
--------

XML output
~~~~~~~~~~

Use ``-f xml``::

    $ python3 analysis.py -f xml satcomp2014_benchmarks/sc14-app/001-80-12.cnf

    <?xml version='1.0' encoding='utf-8'?>
    <metrics>
      <file path="satcomp2014_benchmarks/sc14-app/001-80-12.cnf" time="2015-06-21T23:01:46.994936">
        <metric count_existential_literals="0"/>
        <metric count_unique_clauses="478488"/>
        <metric literal_recurrence_percent="0.0004892038301716437"/>
        <metric clause_length_mean="6.5592449549413985"/>
        <metric count_clauses="478488"/>
        <metric count_pure_literals_positive="147"/>
        <metric literal_recurrence_mean="234.07816229116946"/>
        <metric count_unique_literals="26816"/>
        <metric highest_variable="13408"/>
        <metric clause_length_sum="3138520"/>
        <metric lowest_variable="1"/>
        <metric count_pure_literals="300"/>
        <metric positive_literals_ratio="0.502639142015982"/>
        <metric clause_length_std="1.3266195149505624"/>
        <metric count_unique_variables="13408"/>
        <metric literal_recurrence_sd="247.31242553401754"/>
      </file>
    </metrics>

Redirect to a file
~~~~~~~~~~~~~~~~~~

Use ``-o <filename>``::

    $ python3 analysis.py -o 001-80-12.metrics.json satcomp2014_benchmarks/sc14-app/001-80-12.cnf
    $ cat 001-80-12.metrics.json

    {
      "metrics": [
        {
          "literal_recurrence_percent": 0.0004892038301716437,
          "count_unique_clauses": 478488,
          "literal_recurrence_sd": 247.31242553401754,
          "clause_length_sum": 3138520,
          "count_pure_literals": 300,
          "positive_literals_ratio": 0.502639142015982,
          "count_unique_variables": 13408,
          "clause_length_std": 1.3266195149505624,
          "count_unique_literals": 26816,
          "count_pure_literals_positive": 147,
          "lowest_variable": 1,
          "@time": "2015-06-21T23:20:05.889001",
          "highest_variable": 13408,
          "literal_recurrence_mean": 234.07816229116946,
          "count_clauses": 478488,
          "@path": "satcomp2014_benchmarks/sc14-app/001-80-12.cnf",
          "count_existential_literals": 0,
          "clause_length_mean": 6.5592449549413985
        }
      ]
    }

Reading from stdin
~~~~~~~~~~~~~~~~~~

Use ``-`` as positional argument::

    $ python3 analysis.py < satcomp2014_benchmarks/sc14-app/001-80-12.cnf

    No DIMACS filepaths provided. Expecting DIMACS content at stdin …
    {
      "metrics": [
        {
          "clause_length_std": 1.3266195149505624,
          "count_unique_clauses": 478488,
          "count_unique_literals": 26816,
          "@time": "2015-06-21T23:14:36.023449",
          "literal_recurrence_percent": 0.0004892038301716437,
          "count_pure_literals_positive": 147,
          "clause_length_sum": 3138520,
          "lowest_variable": 1,
          "count_clauses": 478488,
          "count_existential_literals": 0,
          "count_pure_literals": 300,
          "positive_literals_ratio": 0.502639142015982,
          "literal_recurrence_sd": 247.31242553401754,
          "highest_variable": 13408,
          "literal_recurrence_mean": 234.07816229116946,
          "clause_length_mean": 6.5592449549413985,
          "count_unique_variables": 13408
        }
      ]
    }

Reading multiple files
~~~~~~~~~~~~~~~~~~~~~~

Provide them as positional arguments::

    $ python3 analysis.py satcomp2014_benchmarks/sc14-app/001-80-12.cnf satcomp2014_benchmarks/sc14-app/002-23-96.cnf

    {
      "metrics": [
        {
          "literal_recurrence_percent": 0.0004892038301716437,
          "literal_recurrence_sd": 247.31242553401754,
          "count_pure_literals": 300,
          "literal_recurrence_mean": 234.07816229116946,
          "lowest_variable": 1,
          "count_unique_literals": 26816,
          "clause_length_mean": 6.5592449549413985,
          "count_clauses": 478488,
          "highest_variable": 13408,
          "count_unique_variables": 13408,
          "count_pure_literals_positive": 147,
          "count_unique_clauses": 478488,
          "clause_length_std": 1.3266195149505624,
          "clause_length_sum": 3138520,
          "@time": "2015-06-21T23:27:07.614124",
          "@path": "satcomp2014_benchmarks/sc14-app/001-80-12.cnf",
          "count_existential_literals": 0,
          "positive_literals_ratio": 0.502639142015982
        },
        {
          "literal_recurrence_percent": 0.0015364535732969443,
          "literal_recurrence_sd": 227.8888691883187,
          "count_pure_literals": 384,
          "count_existential_literals_positive": 34,
          "literal_recurrence_mean": 203.7460354477612,
          "lowest_variable": 1,
          "count_unique_literals": 8512,
          "clause_length_mean": 6.588312922297297,
          "count_existential_literals_negative": 30,
          "count_clauses": 132608,
          "highest_variable": 4288,
          "count_unique_variables": 4288,
          "count_pure_literals_positive": 187,
          "count_unique_clauses": 132608,
          "clause_length_std": 1.383146716509098,
          "clause_length_sum": 873663,
          "@time": "2015-06-21T23:27:29.174615",
          "@path": "satcomp2014_benchmarks/sc14-app/002-23-96.cnf",
          "count_existential_literals": 64,
          "positive_literals_ratio": 0.5027304578538865
        }
      ]
    }

Reading multiple files on stdin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's try to concatenate them::

    $ cat satcomp2014_benchmarks/sc14-app/001-80-12.cnf satcomp2014_benchmarks/sc14-app/002-23-96.cnf | python3 analysis.py

    No DIMACS filepaths provided. Expecting DIMACS content at stdin …
    Traceback (most recent call last):
      File "analysis.py", line 411, in <module>
        sys.exit(main(args))
      File "analysis.py", line 373, in main
        readDimacs(sys.stdin, analyzers[-1], ignoreheader=args.ignore_header)
      File "analysis.py", line 300, in readDimacs
        assert state == 0, msg.format(lineno)
    AssertionError: Unexpected DIMACS header at line 482710

There are two DIMACS headers.
Use ``-p`` to ignore DIMACS headers::

    $ cat satcomp2014_benchmarks/sc14-app/001-80-12.cnf satcomp2014_benchmarks/sc14-app/002-23-96.cnf | python3 analysis.py -p

    No DIMACS filepaths provided. Expecting DIMACS content at stdin …
    {
      "metrics": [
        {
          "@time": "2015-06-21T23:37:04.205106",
          "lowest_variable": 1,
          "count_pure_literals": 684,
          "count_clauses": 607512,
          "clause_length_mean": 6.5747886461502,
          "count_pure_literals_positive": 334,
          "count_unique_clauses": 603928,
          "highest_variable": 13408,
          "count_unique_variables": 13408,
          "positive_literals_ratio": 0.5026709558183825,
          "clause_length_sum": 3994263,
          "clause_length_std": 1.3376598294196669,
          "literal_recurrence_percent": 0.0004925630970967433,
          "literal_recurrence_sd": 295.890907634993,
          "count_unique_literals": 26816,
          "literal_recurrence_mean": 299.23799224343674,
          "count_existential_literals": 0
        }
      ]
    }

Cheers,
prokls

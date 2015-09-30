cnf-analysis
============

.. contents::
    :backlinks: none

cnf-analysis is a command line tool to analyse CNF files.
CNF files are expected to be written in DIMACS format.
After parsing them, they are read through an IPASIR interface.
On calling the ``release`` method, metrics about the CNF file are computed.
Those metrics are written to a file with extension ``.stats``.

Performance
-----------

* 825 files (25 GB) of SAT competition 2014 were computed in 18 hours.
* 50306 (46 GB) small files of SATlib were computed in less than 20 minutes.

So performance can be a bit of an issue, but this gives you an estimate.
You could split the evaluation space into multiple processes. I didn't.

Memory
------

On my 4GB-RAM machine I was able to process files up to 1 GB,
but some benchmarks are larger (for example ``sc14-app/esawn_uw3.debugged.cnf``
of SAT competition 2014). I used a machine with 16 GB in that case and
it worked fine. I never got into major trouble with 16 GB.


Dependencies
------------

* `python3 <http://python.org/>`_

I think it should work with every 3.x release.
However I tested it with Python 3.4.0 on linux x86_64.

Example
-------

Here you can see a simple example::

    $ python3 analysis.py satcomp2014/sc14-app/001-80-12.cnf

    Info: File 'satcomp2014/sc14-app/001-80-12.cnf.stats' written
    python3 analysis.py satcomp2014/sc14-app/001-80-12.cnf  33.14s user 0.20s system 99% cpu 33.389 total

    $ cat satcomp2014/sc14-app/001-80-12.cnf.stats

    {
      "metrics": [
        {
          "sha1sum": "15ae98b1f6b82200ae91094b3fb9630ccdb1b0cb",
          "time": "2015-08-06T23:54:48.771150",
          "filename": "001-80-12.cnf",
          "metric": {
            "literals_existential_count": 0,
            "variables_recurrence_smallest": 4,
            "variables_unique_count": 13408,
            "literals_unique_count": 26816,
            "literals_unit_unique_negative_count": 147,
            "clauses_length_mean": 6.5592449549413985,
            "variables_recurrence_mean": 234.07816229116946,
            "literals_positive_in_clauses_largest": 7,
            "variables_recurrence_largest": 2601,
            "clauses_length_largest": 8,
            "literals_positive_in_clauses_mean": 3.2969332564244036,
            "variables_lowest": 1,
            "clauses_length_sd": 1.3266195149505624,
            "literals_positive_in_clauses_count": 478488,
            "variables_largest": 13408,
            "variables_recurrence_sum": 3138520,
            "variables_recurrence_sd": 247.31242553401754,
            "literals_unit_unique_count": 300,
            "variables_recurrence_percent": 0.0004892038301716437,
            "literals_unit_unique_positive_count": 153,
            "variables_recurrence_count": 13408,
            "literals_positive_in_clauses_sum": 1577543,
            "clauses_length_sum": 3138520,
            "literals_positive_in_clauses_smallest": 0,
            "clauses_count": 478488,
            "literals_positive_in_clauses_sd": 1.628150659160096,
            "clauses_unique_count": 478488,
            "clauses_length_smallest": 1,
            "literals_count": 3138520,
            "literals_positive_ratio": 0.502639142015982,
            "clauses_length_count": 478488
          }
        }
      ]
    }

As you can see there are three meta values which is the sha1sum of the
evaluated file, the timestamp of the evaluation and the basename of the file.
The evaluated metrics are stored as key-value pairs.
You can get a specification of all metrics using::

    $ python3 analysis.py --description

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
    […]

``--help`` will of course also help you.

Problematic files
-----------------

DIMACS is a pseudo-standard. There is no formal specification for the format.
So there exist problematic files meaning they use an unconventional syntax compared to the majority of CNF files.

Per default, ``analysis.py`` checks the header specifying the number of variables and clauses.
The header's number of clauses has to be the actual number of clauses including duplicates.
The header's number of variables has to the actual number of variables mentioned.
Some files have a higher value for the number of variables because some variables shall be created,
but can take an arbitrary boolean value (rendering them useless in the first place).

You can handle such cases by specifying header check skipping using ``-p``::

    $ cat test.cnf

    p cnf 1 2
    1 0

    $ python3 analysis.py test.cnf

    Traceback (most recent call last):
      File "analysis.py", line 120, in <module>
      […]
      File "processing.py", line 167, in check_header
        assert valid_clause_number, msg.format(self.header[1], computed_header[1])
    AssertionError: Claimed number of clauses is 2, but is actually 1. Do duplicates exists?

    $ python3 analysis.py test.cnf -p

    Info: File 'test.cnf.stats' written

Furthermore some DIMACS interpretation allow the final "0" of a clause to be specified in a separate new line.
And ``mcnf`` generates files which are terminated by a line "%" followed by a line "0".
So one problematic CNF file would be::

    $ cat test.cnf

    p cnf 1 1
    1
    0
    %
    0

    $ python3 analysis.py test.cnf

    Traceback (most recent call last):
      File "analysis.py", line 120, in <module>
        sys.exit(main(args))
      File "analysis.py", line 88, in main
        raise e
      File "analysis.py", line 81, in main
        read(fp, analyzer, ignoreheader=args.ignoreheader)
      File "input.py", line 46, in read_dimacs
        assert re.search(clause_regex, line), msg.format(clause_regex, lineno)
    AssertionError: Clause lines must have layout ^\s*((-?\d+)\s+)+?0\s*$ at line 2

    $ python3 analysis.py test.cnf -m

    Info: File 'test.cnf.stats' written

Files in such a syntax can be handled by the *multiline* mode. Specify ``-m`` to enable this mode.

Features
--------

XML output
~~~~~~~~~~

Use ``-f xml``::

    $ python3 analysis.py -f xml satcomp2014/sc14-app/001-80-12.cnf

    Info: File 'satcomp2014/sc14-app/001-80-12.cnf.stats' written
    python3 analysis.py -f xml satcomp2014/sc14-app/001-80-12.cnf  34.61s user 0.21s system 99% cpu 35.072 total

    $ cat 001-80-12.cnf.stats

    <?xml version="1.0" encoding="utf-8"?>
    <metrics>
      <file filename="001-80-12.cnf" sha1sum="15ae98b1f6b82200ae91094b3fb9630ccdb1b0cb" time="2015-08-07T00:50:46.290754">
        <metric literals_existential_count="0"/>
        <metric literals_positive_ratio="0.502639142015982"/>
        […]
        <metric literals_unit_unique_positive_count="153"/>
      </file>
    </metrics>

Reading from stdin
~~~~~~~~~~~~~~~~~~

Use ``-`` as positional argument::

    $ python3 analysis.py - < satcomp2014/sc14-app/001-80-12.cnf

    No DIMACS filepaths provided. Expecting DIMACS content at stdin …
    {
      "metrics": [
        {
          "time": "2015-08-07T01:13:30.006901",
          "metric": {
            "clauses_length_sum": 3138520,
            "variables_recurrence_percent": 0.0004892038301716437,
            […]
            "variables_recurrence_largest": 2601
          }
        }
      ]
    }

Incremental progress
~~~~~~~~~~~~~~~~~~~~

Assume you use a wildcard to list a range of files. During the progress you abort the procedure.
Later on you want to continue. But you want to skip files which already have valid data.
Use ``--skip-existing``::

    $ python3 analysis.py hanoi4.cnf --skip-existing

    Info: File hanoi4.cnf.stats already exists. Skipping.

Combining results
-----------------

You end up with a lot of metrics in ``.stats`` files.
Assume you want to combine all results into one files.
Use ``combine.py``::

    $ python3 combine.py 001-80-12.cnf.stats hanoi4.cnf.stats

    {
      "metrics": [
        {
          "filename": "001-80-12.cnf",
          "metric": {
            "clauses_count": 478488,
            "clauses_length_largest": 8,
            […]
          },
          "sha1sum": "15ae98b1f6b82200ae91094b3fb9630ccdb1b0cb",
          "time": "2015-08-07T01:24:01.552011"
        },
        {
          "filename": "hanoi4.cnf",
          "metric": {
            "clauses_count": 4934,
            "clauses_length_largest": 7,
            […]
          },
          "sha1sum": "d6023908b0c475619d7493f63685fd16936daa9c",
          "time": "2015-08-07T01:23:56.925434"
        }
      ]
    }

You can use ``-f xml`` to get XML output.

Cheers,
prokls

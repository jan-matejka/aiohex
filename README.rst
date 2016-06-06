aiohex - an aiohttp example
###########################

This package demonstrates usage of

* `aiohttp` to serve three web pages [3]_.

* custom session management [1]_.

* `sqlalchemy` and `aiopg` to record page hits with much information
  about the client who made them into a postgresql database.

* `networkx` to process the hits into markov chains representing page
  transitions [2]_.

* `pytest` and `cram` to self-test the program.

* and last but not least, `sphinx` to generate documentation.

Installation
============

.. code:: shell

   python setup.py install

Altough for tests you will also need `zsh`.

Configuration
=============

An `INI` formatted config file is loaded according to `XDG`
specification from `aiohex/config.ini` unless overriden via `-c` option.

There is a single section - `core` where `dsn` should be set to your
data source name, and `ssl` to `off` unless you also set up ssl for the
server.

.. code:: ini

   [core]
   dsn = postgresql://localhost/yadayada
   ssl = off

Usage
=====

Basic overview

::

  $ ./aiohex.py --help
  usage: aiohex.py [-h] [-c CONFIG] {transitions,serve,sessions} ...

  Example aiohttp web app

  positional arguments:
    {transitions,serve,sessions}
      serve               Start HTTP server
      transitions         Display page transitions graph
      sessions            List sessions in descending order by time of latest
                          hit.

  optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG, --config CONFIG
                          Config path

Displaying transitions

::

  $ aiohex transitions
  Aggregated transitions:

  +---+                    +------+
  | 1 | ---  50 % --->     | exit |
  +---+                    +------+

                           +---+
        ---  25 % --->     | 3 |
                           +---+

                           +---+
        ---  25 % --->     | 2 |
                           +---+
  +---+                    +---+
  | 2 | ---  67 % --->     | 3 |
  +---+                    +---+

                           +---+
        ---  33 % --->     | 1 |
                           +---+

  +---+                    +---+
  | 3 | ---  40 % --->     | 1 |
  +---+                    +---+

                           +---+
        ---  20 % --->     | 2 |
                           +---+

Displaying transitions for single session

::

  $ aiohex transitions --session-id 00000000-0000-0000-0000-000000000001
  Transitions for session 00000000-0000-0000-0000-000000000001:

  +---+                    +------+
  | 1 | ---  33 % --->     | exit |
  +---+                    +------+

                           +---+
        ---  33 % --->     | 3 |
                           +---+

                           +---+
        ---  33 % --->     | 2 |
                           +---+
  +---+                    +---+
  | 2 | --- 100 % --->     | 3 |
  +---+                    +---+


  +---+                    +---+
  | 3 | ---  50 % --->     | 1 |
  +---+                    +---+


Exit codes
==========

* 0 on success

* 2 in case of configuration error

* 1 in case of any other error

Tests
=====

.. code:: shell

   make check

Documentation
=============

.. code::

   make doc

.. [1] `aiohttp_session` was deemed unfit but served as source of
   inspiration.

.. [2] `networkx` could probably be also used to draw the graphs via
   matloptlib or graphviz-like libraries but the author opted to hack
   very specialized ASCII block diagram generator.

.. [3] Shutdown handlers are not addressed since all that needs shutting
   down are the postgresql connection, which is by the aiopg context
   manager used to acquire them.

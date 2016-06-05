# -*- coding: utf-8 -*-

"""
Databse accessors / helpers
"""

import asyncio
import io
import itertools
import sys

import sqlalchemy as sa
from sqlalchemy import sql
from sqlalchemy.dialects import postgresql as pgdia
from aiopg.sa import create_engine

from . import markov

metadata = sa.MetaData()

hits = sa.Table(
  'hits'
, metadata
, sa.Column('id'        , sa.Integer      , primary_key = True)
, sa.Column('page_no'   , sa.Integer      , nullable = False)
, sa.Column('session_id', pgdia.UUID(True), nullable = False)
, sa.Column('ip'        , pgdia.INET      , nullable = False)
, sa.Column('socket'    , sa.Integer      , nullable = False)
, sa.Column('headers'   , sa.Text         , nullable = False)
)
# TODO: use more reasonable format for headers
# TODO: more browser fingerprinting.
#       http://anoncheck.security-portal.cz/ is a good reference for
#       starters
#       and here probably are further hints
#       https://panopticlick.eff.org/about#methodology

def connect(dsn):
  """
  :param dsn:
  :type dsn: DSN

  :returns: aiopg.sa.Engine
  """
  _create_tables(dsn)
  return asyncio.get_event_loop() \
    .run_until_complete(create_engine(dsn))

class DSN(str):
  """
  Postgresql Connection URI. See https://www.postgresql.org/docs/9.4/static/libpq-connect.html#AEN41223
  """

async def register_hit(engine, page_no, session_id, ip, socket, headers):
  """
  :param engine:
  :type  engine: aiopg.sa.Engine

  :param page_no:
  :type  page_no: int

  :param session_id:
  :type  session_id: uuid.UUID

  :param ip:
  :type  ip: str

  :param socket:
  :type  socket: int

  :param headers:
  :type  headers: dict

  :rtype: None
  """

  q = hits.insert().values(
    page_no    = page_no
  , session_id = session_id
  , ip         = ip
  , socket     = socket
  , headers    = str(headers)
  )

  async with engine.acquire() as conn:
    await conn.execute(q)

async def get_transitions(engine, exit_state = None):
  """
  :param exit_state: value to represent exit_state with.
  :type  exit_state: object

  :returns: dict(session_id = transition_graph)
  :rtype: dict(UUID = markov.Graph]
  """
  # TODO: namedtuple
  q = sql.Select([hits.c.page_no, hits.c.session_id]) \
    .order_by(hits.c.session_id, hits.c.id)

  async with engine.acquire() as conn:
    xs = await conn.execute(q)

  return _hits_to_graphs(xs, exit_state)

async def get_sessions(engine):
  """
  :rtype: [UUID]
  """
  q = sql.Select([
    hits.c.session_id
  , sql.functions.count().label("hits")
  ]) \
  .group_by(hits.c.session_id) \
  .order_by(sql.functions.max(hits.c.id).desc())

  async with engine.acquire() as conn:
    return await conn.execute(q)

def _hits_to_graphs(xs, exit_state):
  """
  :param xs: [(page_id, session_id)]
    must be sorted by session_id and then in chronological order
  :type  xs: [(int, uuid.UUID)]

  :rtype: markov.Graph

  >>> gs = _hits_to_graphs([(1, 1), (3, 1), (1, 2)], 0)
  >>> list(gs.keys())
  [1, 2]
  >>> gs[1].nodes()
  [0, 1, 3]
  >>> gs[2].nodes()
  [0, 1]
  >>> gs[1].edges()
  [(1, 3), (3, 0)]
  >>> gs[2].edges()
  [(1, 0)]
  >>> isinstance(gs[1], markov.Graph)
  True
  >>> _hits_to_graphs([], 0)
  {}
  """
  # group by session id
  xs = [[y for y in x[1]] for x in itertools.groupby(xs, lambda x: x[1])]

  # extract session ids
  xs = ((x[0][1], (y[0] for y in x)) for x in xs)

  # convert to transition tuples
  xs = ((sid, _insert_peeks(ts, markov.Graph.exit_state))
    for sid, ts in xs
  )

  # convert to graph
  xs = ((sid, markov.Graph.from_edges(ts))
    for sid, ts in xs
  )

  return dict(xs)

def _insert_peeks(xs, end_peek = None):
  """
  Converts each element `x` of `xs` into
  a tuple `(x, next_element_of_xs_aka_peek)`

  More formally, converts xs into ys where::

    ys[N] is (x[N], x[N+1])     for N+1 < len(xs) and
    ys[N] is (x[N], end_peek)   for N+1 == len(xs)

  :param xs:
  :type  xs: [object]

  :param end_peek: item to use instead of peek for last element
  :type  end_peek: object

  >>> list(_insert_peeks((x for x in range(1,4))))
  [(1, 2), (2, 3), (3, None)]
  """
  # TODO: There is more_itertools.peekable but I couldn't get it to
  #       work as expected
  if xs == []:
    return []

  r = next(xs)
  while True:
    peek = next(xs, end_peek)
    yield (r, peek)
    if peek is end_peek:
      break

    r = peek

def _create_tables(*args, **kwargs):
  """
  Connects to postgresql instance identified by `dsn` and creates all
  tables if missing.

  The SQLAlchemy can not execute queries via the async API, so this
  function creates the SQLAlchemy Engine to run the CREATE TABLES and
  then disposes of it.

  :param dsn:
  :type  dsn: DSN
  """

  e = sa.create_engine(*args, **kwargs)
  metadata.create_all(e)
  e.dispose()

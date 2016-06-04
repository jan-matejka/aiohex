# -*- coding: utf-8 -*-

"""
Databse accessors / helpers
"""

import asyncio
import io
import sys

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgdia
from aiopg.sa import create_engine

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

class DSN(str):
  """
  Postgresql Connection URI. See https://www.postgresql.org/docs/9.4/static/libpq-connect.html#AEN41223
  """

def create_tables(*args, **kwargs):
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

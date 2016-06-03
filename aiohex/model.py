# -*- coding: utf-8 -*-

"""
Databse accessors / helpers
"""

import asyncio
import io
import sys

import sqlalchemy as sa
from aiopg.sa import create_engine

metadata = sa.MetaData()

hits = sa.Table(
  'hits'
, metadata
, sa.Column('id', sa.Integer, primary_key = True)
, sa.Column('page_no', sa.Integer, nullable = False)
)

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

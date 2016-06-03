# -*- coding: utf-8 -*-
import asyncio
import sys

from aiohttp import web
from . import model

__version__ = '0.1.0'

def mk_body(pn):
  """
  :param pn: page number
  :param pn: int

  :returns: http response body
  :rtype: bytes
  """
  return '<html><head></head><body><h1>{}</h1><p>{}</p></body></html>'.format(
    pn
  , "".join(['<a href="/{0}">{0}</a>'.format(x) for x in range(1,4)])
  ).encode("utf-8")

async def page_view(r):
  """
  :returns: response for one of the 3 available pages
  """
  try:
    pn = int(r.match_info['pn'])
  except ValueError:
    raise web.HTTPNotFound

  return web.Response(body = mk_body(pn))

async def root_view(r):
  """
  Redirects to first page
  """
  raise web.HTTPFound('/1')

def main():
  dsn = "postgresql://localhost/aiohex"

  # setup db
  model.create_tables(dsn)
  engine = asyncio.get_event_loop() \
    .run_until_complete(model.create_engine(dsn))

  # setup web app
  app = web.Application()
  app.router.add_route('GET', '/'    , root_view)
  app.router.add_route('GET', '/{pn}', page_view)
  app['db'] = engine

  # run
  web.run_app(app)
  sys.exit(0)

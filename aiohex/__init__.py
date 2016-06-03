# -*- coding: utf-8 -*-
import asyncio
import sys

from aiohttp import web

from . import model
from . import session

__version__ = '0.1.0'

def create_body(pn):
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

  return web.Response(body = create_body(pn))

async def root_view(r):
  """
  Redirects to first page
  """
  raise web.HTTPFound('/1')


class Config:
  """
  Configuration object.

  :param dsn:
  :type  dsn: model.DSN

  :param ssl_on: Indicator of wheter site is running on SSL or not.
    Intended to be False for development purposes, True otherwise.
  :type  ssl_on: bool

  :param session_cookie_name:
  :type  session_cookie_name: str
  """
  def __init__(c):
    # TODO: read from from file path given through argv via configparser
    # or something
    c.dsn = model.DSN("postgresql://localhost/aiohex")
    c.ssl_on = False
    c.session_cookie_name = "AIOHEX_ID"

  def create_cookie_config(c):
    """
    :returns: session.CookieConfig
    """
    return session.CookieConfig(
      name     = c.session_cookie_name
    , secure   = c.ssl_on
    , httponly = True
    )

def main():
  c = Config()

  # setup db
  model.create_tables(c.dsn)
  engine = asyncio.get_event_loop() \
    .run_until_complete(model.create_engine(c.dsn))

  # setup session management
  app = web.Application(middlewares = [
    session.create_middleware_factory(c.create_cookie_config())
  ])

  # setup url routing
  app.router.add_route('GET', '/'    , root_view)
  app.router.add_route('GET', '/{pn}', page_view)
  app['db'] = engine

  # run
  web.run_app(app)
  sys.exit(0)

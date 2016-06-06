# -*- coding: utf-8 -*-

import argparse
import asyncio
import configparser
import itertools
import sys
import uuid

from aiohttp import web
from xdg import BaseDirectory

from . import model
from . import session
from . import markov
from . import test_model

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

  peer = r.transport.get_extra_info('peername')
  await model.register_hit(
    r.app['db']
  , pn
  , r['session'].id
  , peer[0]
  , peer[1]
  , dict(r.headers)
  )
  return web.Response(body = create_body(pn))

async def root_view(r):
  """
  Redirects to first page
  """
  raise web.HTTPFound('/1')

class ConfigurationError(RuntimeError):
  pass

class Config:
  """
  Configuration object.

  The parameter names correspond to the config options in `core`
  section.

  :param dsn: Data source name.
  :type  dsn: model.DSN

  :param ssl: Indicator of wheter site is running on SSL or not.
    Intended to be False for development purposes, True otherwise.
  :type  ssl: bool

  :param session_cookie_name:
  :type  session_cookie_name: str

  :param ip: ip to bind to
  :type  ip: str

  :param port: port to bind to
  :type  port: int

  :param model: Database model to use. Relevant only to self-tests.
  """

  _models = dict(
    actual  = model
  , empty   = test_model.Model()
  , fixture = test_model.Fixture()
  )

  def __init__(c, path):
    try:
      c.load(path)
    except KeyError as e:
      raise ConfigurationError("Required option: " + e.args[0]) from e

  def load(c, path):
    """
    Loads config identified by path
    """
    cp = configparser.ConfigParser()
    cp.read(path)
    core = cp.setdefault('core', dict())

    c.dsn = model.DSN(core['dsn'])
    c.ssl = cp.getboolean('core', 'ssl', fallback = True)
    c.session_cookie_name = core.setdefault(
      'session_cookie_name'
    , 'AIOHEX_ID'
    )

    c.ip   = core.setdefault('ip', '127.0.0.1')
    c.port = cp.getint('core', 'port', fallback = 8080)

    c._model = core.setdefault('model', 'actual')
    if c._model not in c._models.keys():
      raise ConfigurationError('Invalid model ' + repr(c._model))

  def create_cookie_config(c):
    """
    :returns: session.CookieConfig
    """
    return session.CookieConfig(
      name     = c.session_cookie_name
    , secure   = c.ssl
    , httponly = True
    )

  @property
  def model(c):
    return c._models[c._model]

  def forget_dsn(c):
    c.dsn = None

def main():
  xdg_config = BaseDirectory.load_first_config("aiohex", "config.ini")

  p = argparse.ArgumentParser(description = 'Example aiohttp web app')
  p.add_argument("-c", "--config", help = 'Config path'
  , default  = xdg_config
  , required = not xdg_config
  )

  sub = p.add_subparsers(dest = 'command')
  sub.add_parser("serve", help = serve.__doc__)

  tp = sub.add_parser("transitions", help = transitions.__doc__)
  tp.add_argument("--session-id", type = uuid.UUID
  , help = "Show transitions for given session-id only"
  )

  sub.add_parser("sessions", help = sessions.__doc__)

  args = p.parse_args(sys.argv[1:])

  try:
    c = Config(args.config)
  except ConfigurationError as e:
    print(e)
    sys.exit(2)

  dispatch = dict(
    serve       = serve
  , transitions = transitions
  , sessions    = sessions
  )

  sys.exit(dispatch[args.command](
    args
  , asyncio.get_event_loop()
  , c
  , c.model
  ))

def serve(args, _, c, model):
  """
  Start HTTP server
  """
  # setup session management
  app = web.Application(middlewares = [
    session.create_middleware_factory(c.create_cookie_config())
  ])

  # setup url routing
  app.router.add_route('GET', '/'    , root_view)
  app.router.add_route('GET', '/{pn}', page_view)
  app['db'] = model.connect(c.dsn)
  c.forget_dsn()

  # run
  web.run_app(app, host = c.ip, port = c.port)
  return 0

def transitions(args, loop, c, model):
  """
  Display page transitions graph
  """
  e = model.connect(c.dsn)

  exit_state = 0
  tgs = loop.run_until_complete(
    model.get_transitions(e, exit_state)
  )

  if args.session_id:
    if args.session_id not in tgs:
      print("Unknown session {!r}".format(args.session_id))
      return 1

    tg = tgs[args.session_id]
    tg.compute_probabilities()

    print("Transitions for session {}:\n".format(args.session_id))
    tg.draw_transitions()

  else:
    g = markov.Graph()
    for tg in tgs.values():
      g.add_weights(tg)
    g.compute_probabilities()

    print("Aggregated transitions:\n")
    g.draw_transitions()

def sessions(args, loop, c, model):
  """
  List sessions in descending order by time of latest hit.
  """
  xs = loop.run_until_complete(
    model.get_sessions(model.connect(c.dsn))
  )
  print("{0:<38} {1}".format("Session id", "Total Hits"))
  for x in xs:
    print("{}   {}".format(x.session_id, x.hits))

def flatten(xs):
  """
  The flat part of flatMap

  :type xs: [[object]]
  :rtype: [object]
  """
  return [y for x in xs for y in x]

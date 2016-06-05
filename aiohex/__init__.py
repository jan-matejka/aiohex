# -*- coding: utf-8 -*-
import argparse
import asyncio
import itertools
import sys
import uuid

from aiohttp import web

from . import model
from . import session
from . import markov

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

  p = argparse.ArgumentParser(description = 'Example aiohttp web app')
  sub = p.add_subparsers(dest = 'command')
  sub.add_parser("serve", help = serve.__doc__)

  tp = sub.add_parser("transitions", help = transitions.__doc__)
  tp.add_argument("--session-id", type = uuid.UUID
  , help = "Show transitions for given session-id only"
  )

  sub.add_parser("sessions", help = sessions.__doc__)

  args = p.parse_args(sys.argv[1:])

  dispatch = dict(
    serve       = serve
  , transitions = transitions
  , sessions    = sessions
  )

  sys.exit(dispatch[args.command](
    args
  , asyncio.get_event_loop()
  , Config()
  ))

def serve(args, _, c):
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

  # run
  web.run_app(app)
  return 0

def transitions(args, loop, c):
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
      print("Unknown session {}".format(args.session_id))
      return 1

    tg = tgs[args.session_id]
    tg.compute_probabilities()

    print("Transitions for session {}:\n".format(args.session_id))
    tg.draw_transitions()

  else:
    g = markov.Graph(flatten(
      [x.edges(data = True) for x in tgs.values()]
    ))
    g.compute_probabilities()

    print("Aggregated transitions:\n")
    g.draw_transitions()

def sessions(args, loop, c):
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

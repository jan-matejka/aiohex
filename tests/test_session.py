# -*- coding: utf-8 -*-

import asyncio
import functools
from http import cookies
import uuid

from aiohttp import web
from aiohttp import protocol
from aiohttp import streams
from aiohttp import parsers
from aiohttp.web_reqrep import Request

from aiohex.session import CookieConfig, create_middleware_factory

async def empty_handler(r):
  return web.Response()

def create_request(raw_request_lines):
  """
  :param raw_request_lines: HTTP Request lines without line ends
  :type  raw_request_lines: list(str)

  :rtype: Request
  """
  class ParserOut:
    """
    :param message:
    :type  message: protocol.RawRequestMessage
    """
    def feed_data(po, m, _):
      po.message = m

    def feed_eof(po, *args):
      pass

  raw_request = "\r\n".join(raw_request_lines + ["\r\n"]).encode("utf-8")

  po = ParserOut()
  p = protocol.HttpRequestParser()

  asyncio.get_event_loop() \
    .run_until_complete(p(po, parsers.ParserBuffer(raw_request)))

  return Request(None, po.message, streams.EmptyStreamReader(), None, None, None)

def test_sessions_middleware():
  loop = asyncio.get_event_loop()

  cc = CookieConfig()

  exp_cookie = cookies.SimpleCookie()
  exp_cookie[cc.name] = None # placeholder
  exp_cookie[cc.name]["HttpOnly"] = True
  exp_cookie[cc.name]["Path"] = "/"

  # Note: zero fill format:
  # http://stackoverflow.com/questions/339007/nicest-way-to-pad-zeroes-to-string
  uuids = [
    uuid.UUID("{{00000000-0000-0000-0000-{0:012d}}}".format(x))
    for x in range(0,4)
  ]
  uuid_gen = functools.partial(list(uuids).pop, 0)

  f = create_middleware_factory(cc, uuid_factory = uuid_gen)
  app = web.Application()
  handler = loop.run_until_complete(f(app, empty_handler))

  #
  session = 0
  request = create_request(['GET /1 HTTP/1.1'])
  response =  loop.run_until_complete(handler(request))
  exp_cookie[cc.name] = uuids[session]
  assert str(response.cookies) == str(exp_cookie) \
  , "client with no cookie gets one"

  #
  session += 1
  response =  loop.run_until_complete(handler(request))
  exp_cookie[cc.name] = uuids[session]
  assert str(response.cookies) == str(exp_cookie) \
  , "next client gets another cookie"

  #
  session += 0
  request = create_request([
    'GET /1 HTTP/1.1'
  , 'Cookie: {}={}'.format(cc.name, uuids[session])
  ])

  response =  loop.run_until_complete(handler(request))
  exp_cookie[cc.name] = uuids[session]
  assert str(response.cookies) == str(exp_cookie) \
  , "same client gets the same cookie"

  #
  session += 1
  request = create_request([
    'GET /1 HTTP/1.1'
  , 'Cookie: {}={}'.format(cc.name, "10000000-0000-0000-0000-000000000000")
  ])

  response =  loop.run_until_complete(handler(request))
  exp_cookie[cc.name] = uuids[session]
  assert str(response.cookies) == str(exp_cookie) \
  , "client with unknown cookie gets a new one"

  #
  session += 1
  request = create_request([
    'GET /1 HTTP/1.1'
  , 'Cookie: {}={}'.format(cc.name, "invalid")
  ])

  response =  loop.run_until_complete(handler(request))
  exp_cookie[cc.name] = uuids[session]
  assert str(response.cookies) == str(exp_cookie) \
  , "client with invalid cookie gets a new one"

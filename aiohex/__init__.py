# -*- coding: utf-8 -*-
import asyncio
import sys

from aiohttp import web

__version__ = '0.1.0'

async def view(r):
  """
  :type r: web.Request
  :rtype: web.Response
  """
  return web.Response(body = b"Hello World")

def main():
  app = web.Application()
  app.router.add_route('GET', '/', view)
  web.run_app(app)
  sys.exit(0)

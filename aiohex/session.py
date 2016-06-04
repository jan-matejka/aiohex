# -*- coding: utf-8 -*-

"""
Minimal possible anonymous session management using in memory session
storage and UUID4 as session ID.

.. todo::

  Re-generate session id to make session hijacking harder.

.. todo::

  Encrypt ID to obfuscate it's structure.

.. todo::

  Sign session ID to prevent spoofing.

.. seealso::

  https://www.owasp.org/index.php/Session_Management_Cheat_Sheet
"""

import uuid

def create_middleware_factory(cc, uuid_factory = uuid.uuid4):
  """
  :param cc:
  :type  cc: CookieConfig
  """
  async def factory(app, handler):
    cs = _CookieStore(cc, app, uuid_factory)
    async def middleware(r):
      """
      :param r:
      :type  r: aiohttp.web.Request
      """
      r['session'] = cs.get_session(r)

      response = await handler(r)
      if response.started:
        raise RuntimeError("Response started. Can not save session.")

      cs.set_cookie(response)
      return response

    return middleware
  return factory

class CookieConfig():
  def __init__(
    cc
  , *
  , name     = "AIOHEX_ID"
  , domain   = None
  , max_age  = None
  , path     = '/'
  , secure   = None
  , httponly = True
  ):
    """
    The parameters correspond to aiohttp.web.Response.set_cookie
    """
    cc._name   = name
    cc._params = dict(
      domain   = domain
    , max_age  = max_age
    , path     = path
    , secure   = secure
    , httponly = httponly
    )

  @property
  def name(cc):
    return cc._name

  @property
  def params(cc):
    return cc._params

class _CookieStore:
  """
  .. todo::

    this might work nicer as context manager inside the middleware
  """
  _store_key = 'session_store'

  def __init__(cs, cc, app, uuid_factory):
    """
    :param cc:
    :type  cc: CookieConfig
    """
    cs._config = cc
    cs._app = app
    cs._create_uuid = uuid_factory

  def get_session(cs, request):
    """
    :param request:
    :type  request: aiohttp.web.Request

    :rtype: Session
    """
    cookie = cs._get_cookie(request)

    if cookie not in cs._get_store():
      # cookie is either new or was forgotten by the session store
      # (due to server restart)
      cookie = cs._create_uuid()

    # remember the cookie, so it can be written to the response
    cs._cookie = cookie

    cs._get_store()[cookie] = Session(cookie)
    return cs._get_store()[cookie]

  def set_cookie(cs, response):
    """
    :param response:
    :type  response: aiohttp.web.Response
    """

    response.set_cookie(
      cs._config.name
    , cs._cookie
    , **cs._config.params
    )


  def _get_store(cs):
    """
    :returns: session store
    :rtype: dict
    """
    if not cs._store_key in cs._app:
      cs._app[cs._store_key] = dict()

    return cs._app[cs._store_key]

  def _get_cookie(cs, request):
    """
    :returns: session id
    :rtype: uuid.UUID
    """
    cookie = request.cookies.get(cs._config.name)
    if cookie is None:
      return None

    try:
      return uuid.UUID("{{{}}}".format(cookie))
    except ValueError:
      return None

class Session():
  def __init__(s, id_):
    """
    :param id:
    :type  id: uuid.UUID
    """
    s.id = id_

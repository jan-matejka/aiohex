# -*- coding: utf-8 -*-

import itertools
import uuid
from . import markov

def mk_uuid():
  """
  yields predictable uuids
  """
  for x in itertools.count(1):
    yield uuid.UUID("{{00000000-0000-0000-0000-{0:012x}}}".format(x))

class Model:
  def __init__(m):
    m.hits = []

  async def get_sessions(m, _):
    return iter(m.hits)

  def connect(m, _):
    return None

class Fixture(Model):
  def __init__(m):
    uuid_gen = mk_uuid()
    m.edges = {
      next(uuid_gen): [
        (1, 0)
      , (1, 3)
      , (1, 2)

      , (2, 3)

      , (3, 3)
      , (3, 1)
      ]
    , next(uuid_gen): [
        (1, 0)

      , (2, 3)
      , (2, 1)

      , (3, 3)
      , (3, 1)
      , (3, 2)
      ]
    }

    # totals
    # 1, 0 = 2      2, 0 = 0      3, 0 = 0
    # 1, 1 = 0      2, 1 = 1      3, 1 = 2
    # 1, 2 = 1      2, 2 = 0      3, 2 = 1
    # 1, 3 = 1      2, 3 = 2      3, 3 = 2

  async def get_transitions(m, _, exit_state = None):
    return dict([
      (sid, markov.Graph.from_edges(m.edges[sid]))
      for sid in m.edges
    ])

  async def get_sessions(m, _):
    return m.edges.keys()

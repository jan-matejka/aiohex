# -*- coding: utf-8 -*-

"""
Markov chains helpers
"""

import networkx as nx
import numpy as np
import itertools

# I don't have a math degree but I know a markov chain when I see one.

class Graph(nx.DiGraph):
  """
  .. warning::

    Works only with numeric nodes. `0` must represent exit state.
  """
  exit_state = 0

  # FIXME: make the graph work with any nodes
  # FIXME: remove the construction helpers.
  #        See nx.convert.to_network_graph.
  #        Also probably related to the:
  # FIXME: add possibility for automatic probability recalculation

  def compute_probabilities(g):
    """
    Populates the edge `(u, v)` data with `probability` field
    indicating the probability of transition from `u` to `v`.

    .. warning::

      Once the graph is manipulated again, the probabilities do not
      reflect the new state.
    """
    totals = dict([(x, 0) for x in g.nodes()])

    for u, v in g.edges_iter():
      totals[u] += 1

    for u, v in g.edges_iter():
      g[u][v]['probability'] = g[u][v]['weight'] / float(totals[u])

  @classmethod
  def from_multidigraph(cls, mdg):
    # http://stackoverflow.com/questions/15590812/networkx-convert-multigraph-into-simple-graph-with-weighted-edges
    g = cls()
    for u, v, data in mdg.edges_iter(data = True):
        if g.has_edge(u,v):
          g[u][v]['weight'] += 1
        else:
          g.add_edge(u, v, weight=1)

    return g

  @classmethod
  def from_edges(cls, xs):
    return cls.from_multidigraph(nx.MultiDiGraph(xs))

  @property
  def size(g):
    """
    :returns: Size of the matrix needed for this graph
    """
    return g.nodes()[-1] + 1

  def create_matrix(g):
    """
    :returns: Markov matrix. The probabilities must be pre-calculated.
    :rtype: np.array
    """
    for n in g.nodes():
      assert isinstance(n, int), "Non-numeric nodes are not supported"

    # group by current state
    es = itertools.groupby(g.edges(data = True), lambda e: e[0])

    mm = np.zeros([g.size, g.size])
    for u, v in g.edges_iter():
      mm[u][v] = g[u][v]['probability']

    return mm

  def draw_transitions(g, writeln = print):
    """
    Draws transitions in the form of ASCII block diagram.
    """
    for i in range(1, g.size):
      g._draw_transitions(i, writeln)

  def _draw_transitions(g, current, writeln):
    # FIXME: find a graphing library. I could find only perls
    # Graph::Easy

    assert current != g.exit_state \
    , "Can not have a transition from exit state"

    mm = g.create_matrix()
    if len(mm) <= current or sum(mm[current]) == 0:
      return

    # FIXME: either remove transitions `Si -> Si` from the probability
    # calculation or display them too

    def gen(mm, current, next):
      return dict(
        next = next if next != 0 else 'exit'
      , p = mm[current][next] * 100
      )

    def draw_block(data, prefix = '\n'):
      if(data['p'] == 0):
        return ""

      data['next_len'] = "-" * len(str(data['next']))
      return prefix + """                    +-{next_len}-+
 --- {p:3.0f} % --->     | {next} |
                    +-{next_len}-+""".format(**data)


    def join(left, right):
      out = []
      right = right.lstrip('\n')

      for x, y in itertools.zip_longest(
        [x.rstrip('\n') for x in left.splitlines()]
      , [x.lstrip("\n") for x in right.splitlines()]
      , fillvalue = ""
      ):
        out.append(x + y)

      out = "\n".join(out)
      return out

    def indent(len_, xs):
      return "\n".join([" " * len_ + x for x in xs.splitlines()])

    states = list(set(range(1, len(mm))) - set([current])) + [0]

    current_tpl = """+-{cur_len}-+
| {current} |
+-{cur_len}-+
""".format(current = current, cur_len = "-" * len(str(current)))

    blocks = sorted([draw_block(gen(mm, current, x)) for x in states])
    blocks.reverse()

    writeln(join(current_tpl, blocks.pop(0)))

    while len(blocks):
      writeln(indent(len(str(current)) + 4, blocks.pop(0)))

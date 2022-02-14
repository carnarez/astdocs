"""Prepare an output to visualize the dependency graph of a module/package.

Visualization is intended to be generated via [`D3.js`](https://d3js.org/). See the
~~code in this folder, or refer to the~~ example by the creator of the library himself
[there](https://observablehq.com/@d3/disjoint-force-directed-graph).

Requirements
------------
* `astdocs`

Notes
-----
One can abuse the example at the page linked above: replace the data (browse a bit, find
the right cell, click on the small paperclip icon).

Known problems
--------------
This small toy thing breaks on `from .. import *` statements (cannot guess which
objects are imported; but this is bad `Python` habits anyhow).
"""

import hashlib
import json
import sys

import astdocs

# keep track of the generated content
_nodes = []
_edges = []


def is_local(p: str, objects: list[str]) -> bool:
    """Check whether an object is local, or external, looking at its path.

    Parameters
    ----------
    p : str
        String representation of the object path.
    objects : list[str]
        List of local objects to check for.

    Returns
    -------
    : bool
        Whether the object is local or external to the `Python` parsed package(s).
    """
    if p in objects:
        return True

    if not p.endswith("."):
        p += "."

    for o in objects:
        if p.startswith(f"{o}."):
            return True
        for m in o.split("."):
            if p.startswith(f"{m}."):
                return True

    return False


def add_node(nodes: list[dict[str, int | str]], o: str, g: int):
    """Add a node to the pool if not yet present.

    Parameters
    ----------
    nodes : list[dict[str, str]]
        List of defined nodes.
    o : str
        String representation of the object path.
    g : int
        Value indicating the package ancestry.

    Returns
    -------
    nodes : list[dict[str, str]]
        List of defined nodes, updated (or not).
    """
    if len(o.strip(".")):

        h = hashlib.md5(f"{o}".encode()).hexdigest()  # why not

        if h not in _nodes:
            nodes.append({"id": o, "group": g})
            _nodes.append(h)

    return nodes


def add_edge(edges: list[dict[str, str]], so: str, to: str):
    """Add an edge to the pool if not yet present.

    Parameters
    ----------
    edges : list[dict[str, str]]
        List of defined edges.
    so : str
        String representation of the *source* object path.
    to : str
        String representation of the *target* object path.

    Returns
    -------
    edges : list[dict[str, str]]
        List of defined edges, updated (or not).
    """
    if len(so.strip(".")) and len(to.strip(".")) and so != to:

        h = hashlib.md5((f"{so}->{to}").encode()).hexdigest()

        if h not in _edges and to != so:
            edges.append({"source": so, "target": to})
            _edges.append(h)

    return edges


def graph(
    objects: dict[str, dict[str, dict[str, str]]],
) -> dict[str, list[dict[str, int | str]]]:
    """Generate graph, *e.g.*, nodes and edges.

    Parameters
    ----------
    objects : dict[str, dict[str, dict[str, str]]]
        Dictionary of objects encountered in all modules parsed by `astdocs`.

    Returns
    -------
    : dict[str, list[dict[str, str]]]
        `JSON`-formatted content organised for `D3.js`.

    Notes
    -----
    * Nodes are defined as `{"id": ..., "group": ...}`, `id` being the name of the
      object.
    * Edges are defined as `{"source": ..., "target": ...}`, both being object names.
    * This gymnastics easily breaks on `from ... import *` and other ugliness.
    """
    modules = list(objects.keys())

    edges: list[dict[str, str]] = []
    nodes: list[dict[str, int | str]] = []

    for g, m in enumerate(objects):
        for t in ["classes", "functions", "imports"]:
            for lp, ap in objects[m][t].items():
                group = g + 1 if is_local(ap, modules) else 0

                # actual object (absolute path thereto)
                nodes = add_node(nodes, ap, group)

                # ancestry
                if ap.count("."):
                    x = ap.split(".")
                    for i in range(len(x) - 1):
                        pp = ".".join(x[: i + 1])
                        cp = ".".join(x[: i + 2])
                        nodes = add_node(nodes, pp, group)
                        nodes = add_node(nodes, cp, group)
                        edges = add_edge(edges, pp, cp)

    return {"nodes": nodes, "links": edges}


if __name__ == "__main__":
    try:
        astdocs.render(sys.argv[1])
    except IsADirectoryError:
        astdocs.render_recursively(sys.argv[1])

print(json.dumps(graph(astdocs.objects)))

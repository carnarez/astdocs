"""Prepare an output to visualize the dependency graph of a module/package.

Visualization is intended to be generated via [`D3.js`](https://d3js.org/). See the
~~code in this folder, or refer to the~~ example by the creator of the library himself
[there](https://observablehq.com/@d3/force-directed-graph).

Notes
-----
One can abuse the example at the page linked above: replace the data (browse a bit, find
find the right cell, click on the small paperclip icon). If the nodes are flying all
over when applying the forces on the graph data, try to modify the parameters of the
simulation:

```javascript
const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id)
        .distance(10)  // distance between linked nodes
    )
    .force("charge", d3.forceManyBody()
        .strength(-5)  // strength of the +attractive/-repulsive force (default: -30)
        .distanceMax(100)  // max distance to apply the forces (default: none)
    )
    .force("center", d3.forceCenter(width / 2, height / 2));
```

See the meaning of those parameters [here](https://github.com/d3/d3-force).
"""

import json
import sys
import typing
from hashlib import md5  # actually not needed, just as example

import astdocs

# keep track of the generated content
_nodes = []
_edges = []


def is_local(o: str, objects: typing.List[str]) -> bool:
    """Check whether an object is local, or external, looking at its path.

    Parameters
    ----------
    o : str
        String representation of the object path.
    objects : typing.List[str]
        List of local objects to check for.

    Returns
    -------
    : bool
        Whether the object is local or external to the `Python` parsed package(s).
    """
    return any([o.startswith(f"{m}.") for m in objects]) or o in objects


def add_node(nodes: typing.List[typing.Dict[str, str]], o: str, g: int):
    """Add a node to the pool if not yet present.

    Parameters
    ----------
    nodes : typing.List[typing.Dict[str, str]]
        List of defined nodes.
    o : str
        String representation of the object path.
    g : int
        Value indicating the package ancestry.

    Returns
    -------
    nodes : typing.List[typing.Dict[str, str]]
        List of defined nodes, updated (or not).
    """
    h = md5(f"{o}".encode()).hexdigest()  # why not

    if h not in _nodes:
        nodes.append({"id": o, "group": g})
        _nodes.append(h)

    return nodes


def add_edge(edges: typing.List[typing.Dict[str, str]], so: str, to: str):
    """Add an edge to the pool if not yet present.

    Parameters
    ----------
    edges : typing.List[typing.Dict[str, str]]
        List of defined edges.
    so : str
        String representation of the *source* object path.
    to : str
        String representation of the *target* object path.

    Returns
    -------
    edges : typing.List[typing.Dict[str, str]]
        List of defined edges, updated (or not).
    """
    h = md5((f"{so}->{to}").encode()).hexdigest()

    if h not in _edges and to != so:
        edges.append({"source": so, "target": to})
        _edges.append(h)

    return edges


def graph(
    objects: typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]],
) -> typing.Dict[str, typing.List[typing.Dict[str, str]]]:
    """Generate graph, *e.g.*, nodes and edges.

    Parameters
    ----------
    objects : typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]]
        Dictionary of objects encountered in all modules parsed by `astdocs`.

    Returns
    -------
    : typing.Dict[str, typing.List[typing.Dict[str, str]]]
        `JSON`-formatted content organised for `D3.js`.

    Notes
    -----
    * Nodes are defined as `{"id": ..., "group": ...}`, `id` being the name of the
      object.
    * Edges are defined as `{"source": ..., "target": ...}`, both being object names.
    * This gymnastics easily breaks on `from ... import *` and other ugliness.
    """
    modules = list(objects.keys())

    edges = []
    nodes = []

    for g, m in enumerate(objects):
        for t in ["classes", "functions", "imports"]:
            for lp, ap in objects[m][t].items():
                lp = f"{m}.{lp}"

                # actual object (absolute path thereto)
                nodes = add_node(nodes, ap, g + 1 if is_local(ap, modules) else 0)

                # module (local) representation of the object
                nodes = add_node(nodes, lp, g + 1 if is_local(lp, modules) else 0)

                # actual object -> its module representation
                edges = add_edge(edges, ap, lp)

                # module -> object representation if directly linked
                if lp.count(".") == 1:
                    edges = add_edge(edges, m, lp)

                if ap.count("."):
                    x = ap.split(".")
                    for i in range(len(x) - 1):
                        pp = ".".join(x[: i + 1])
                        cp = ".".join(x[: i + 2])

                        # parent object
                        nodes = add_node(
                            nodes, pp, g + 1 if is_local(pp, modules) else 0
                        )

                        # child object
                        nodes = add_node(
                            nodes, cp, g + 1 if is_local(cp, modules) else 0
                        )

                        # actual object -> its module representation
                        edges = add_edge(edges, pp, cp)

    return {"nodes": nodes, "links": edges}


if __name__ == "__main__":
    try:
        astdocs.render(sys.argv[1])
    except IsADirectoryError:
        astdocs.render_recursively(sys.argv[1])

print(json.dumps(graph(astdocs._objects)))

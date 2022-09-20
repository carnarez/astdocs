# Module `object_graph`

Prepare an output to visualize the dependency graph of a module/package.

Visualization is intended to be generated via [`D3.js`](https://d3js.org/). See the
~~code in this folder, or refer to the~~ example by the creator of the library himself
[there](https://observablehq.com/@d3/disjoint-force-directed-graph).

**Requirements**

- `astdocs`

**Notes**

One can abuse the example at the page linked above: replace the data (browse a bit, find
the right cell, click on the small paperclip icon).

**Known problems**

This small toy thing breaks on `from .. import *` statements (cannot guess which objects
are imported; but this is bad `Python` habits anyhow).

**Functions**

- [`is_local()`](#object_graphis_local): Check whether an object is local, or external,
  looking at its path.
- [`add_node()`](#object_graphadd_node): Add a node to the pool if not yet present.
- [`add_edge()`](#object_graphadd_edge): Add an edge to the pool if not yet present.
- [`graph()`](#object_graphgraph): Generate graph, *e.g.*, nodes and edges.

## Functions

### `object_graph.is_local`

```python
is_local(p: str, objects: list[str]) -> bool:
```

Check whether an object is local, or external, looking at its path.

**Parameters**

- `p` \[`str`\]: String representation of the object path.
- `objects` \[`list[str]`\]: List of local objects to check for.

**Returns**

- \[`bool`\]: Whether the object is local or external to the `Python` parsed package(s).

### `object_graph.add_node`

```python
add_node(nodes: list[dict[str, int | str]], o: str, g: int):
```

Add a node to the pool if not yet present.

**Parameters**

- `nodes` \[`list[dict[str, str]]`\]: List of defined nodes.
- `o` \[`str`\]: String representation of the object path.
- `g` \[`int`\]: Value indicating the package ancestry.

**Returns**

- `nodes` \[`list[dict[str, str]]`\]: List of defined nodes, updated (or not).

### `object_graph.add_edge`

```python
add_edge(edges: list[dict[str, str]], so: str, to: str):
```

Add an edge to the pool if not yet present.

**Parameters**

- `edges` \[`list[dict[str, str]]`\]: List of defined edges.
- `so` \[`str`\]: String representation of the *source* object path.
- `to` \[`str`\]: String representation of the *target* object path.

**Returns**

- `edges` \[`list[dict[str, str]]`\]: List of defined edges, updated (or not).

### `object_graph.graph`

```python
graph(
    objects: dict[str, dict[str, dict[str, str]]],
) -> dict[str, list[dict[str, int | str]]]:
```

Generate graph, *e.g.*, nodes and edges.

**Parameters**

- `objects` \[`dict[str, dict[str, dict[str, str]]]`\]: Dictionary of objects
  encountered in all modules parsed by `astdocs`.

**Returns**

- \[`dict[str, list[dict[str, str]]]`\]: `JSON`-formatted content organised for `D3.js`.

**Notes**

- Nodes are defined as `{"id": ..., "group": ...}`, `id` being the name of the object.
- Edges are defined as `{"source": ..., "target": ...}`, both being object names.
- This gymnastics easily breaks on `from ... import *` and other ugliness.

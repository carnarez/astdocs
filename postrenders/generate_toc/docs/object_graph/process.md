# Module `object_graph.process`

Prepare an output to visualize the dependency graph of a module/package.

Visualization is intended to be generated via [`D3.js`](https://d3js.org/). See the
~~code in this folder, or refer to the~~ example by the creator of the library himself
[there](https://observablehq.com/@d3/force-directed-graph).

**Notes:**

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

**Functions:**

- [`is_local()`](#object_graphprocessis_local)
- [`add_node()`](#object_graphprocessadd_node)
- [`add_edge()`](#object_graphprocessadd_edge)
- [`graph()`](#object_graphprocessgraph)

## Functions

### `object_graph.process.is_local`

```python
is_local(o: str, objects: typing.List[str]) -> bool:
```

Check whether an object is local, or external, looking at its path.

**Parameters:**

- `o` \[`str`\]: String representation of the object path.
- `objects` \[`typing.List[str]`\]: List of local objects to check for.

**Returns:**

- \[`bool`\]: Whether the object is local or external to the `Python` parsed package(s).

### `object_graph.process.add_node`

```python
add_node(nodes: typing.List[typing.Dict[str, str]], o: str, g: int):
```

Add a node to the pool if not yet present.

**Parameters:**

- `nodes` \[`typing.List[typing.Dict[str, str]]`\]: List of defined nodes.
- `o` \[`str`\]: String representation of the object path.
- `g` \[`int`\]: Value indicating the package ancestry.

**Returns:**

- `nodes` \[`typing.List[typing.Dict[str, str]]`\]: List of defined nodes, updated (or
  not).

### `object_graph.process.add_edge`

```python
add_edge(edges: typing.List[typing.Dict[str, str]], so: str, to: str):
```

Add an edge to the pool if not yet present.

**Parameters:**

- `edges` \[`typing.List[typing.Dict[str, str]]`\]: List of defined edges.
- `so` \[`str`\]: String representation of the *source* object path.
- `to` \[`str`\]: String representation of the *target* object path.

**Returns:**

- `edges` \[`typing.List[typing.Dict[str, str]]`\]: List of defined edges, updated (or
  not).

### `object_graph.process.graph`

```python
graph(
    objects: typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]],
) -> typing.Dict[str, typing.List[typing.Dict[str, str]]]:
```

Generate graph, *e.g.*, nodes and edges.

**Parameters:**

- `objects` \[`typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]]`\]: Dictionary of
  objects encountered in all modules parsed by `astdocs`.

**Returns:**

- \[`typing.Dict[str, typing.List[typing.Dict[str, str]]]`\]: `JSON`-formatted content
  organised for `D3.js`.

**Notes:**

- Nodes are defined as `{"id": ..., "group": ...}`, `id` being the name of the object.
- Edges are defined as `{"source": ..., "target": ...}`, both being object names.
- This gymnastics easily breaks on `from ... import *` and other ugliness.

A few snippets and other post-rendering I implemented in the past and found worth
keeping.

# Environment

If further requirements (aside from `astdocs`) are necessary one can jump into a clean
environment, either:

```shell
$ python -m venv .venv
$ .venv/bin/pip install -U pip
$ .venv/bin/pip install --no-cache-dir git+https://github.com/carnarez/astdocs
$ .venv/bin/pip install --no-cache-dir -r requirements.txt
```

or even:

```shell
$ docker run --entrypoint /bin/bash -it --rm -v `pwd`:/usr/src --workdir /usr/src python:3.8-slim
> apt update
> apt install git
> pip install --no-cache-dir git+https://github.com/carnarez/astdocs
> pip install --no-cache-dir ...
```

if you are like me fond of [`Docker`](https://www.docker.com/) and do **not** like to
sprinkle your entire filetree with random virtual environments. In this latter case keep
in mind the user creating content (might need to play around with `chown`).

# Snippets

- [`generate_toc`](#generate_toc)
  - [`generate_toc.toc`](#generate_toctoc)
- [`linted_output`](#linted_output)
  - [`linted_output.lint`](#linted_outputlint)
  - [`linted_output.render`](#linted_outputrender)
- [`object_graph`](#object_graph)
  - [`object_graph.is_local`](#object_graphis_local)
  - [`object_graph.add_node`](#object_graphadd_node)
  - [`object_graph.add_edge`](#object_graphadd_edge)
  - [`object_graph.graph`](#object_graphgraph)
- [`to_html`](#to_html)

# Module `generate_toc`

Generate a table of contents from listed objects.

**Functions:**

- [`toc()`](#generate_toctoc)

## Functions

### `generate_toc.toc`

```python
toc(objects: typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]]) -> str:
```

Filter objects and generate the table of content.

**Parameters:**

- `objects` \[`typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]]`\]: Dictionary of
  objects encountered in all modules parsed by `astdocs`.

**Returns:**

- \[`str`\]: `Markdown`-formatted table of content.

# Module `linted_output`

Pipe the output of `astdocs` to a linter.

As any other strictly-defined syntax, `Markdown` can (should?) be linted. This small
post-rendering does just that. (This will not be integrated to `astdocs` as it adds a
dependency, which is **out of scope**.)

The `Python` linter chosen for this example is
[`Mdformat`](https://github.com/executablebooks/mdformat), code style described
[there](https://mdformat.readthedocs.io/en/stable/users/style.html).

**Requirements:**

- [`mdformat`](https://github.com/executablebooks/mdformat)

**Functions:**

- [`lint()`](#linted_outputlint)
- [`render()`](#linted_outputrender)

## Functions

### `linted_output.lint`

```python
lint(md: str) -> str:
```

Lint the `Markdown`.

**Parameters:**

- `md` \[`str`\]: The `Markdown` as outputted by `astdocs`.

**Returns:**

- \[`str`\]: Linted `Markdown`.

### `linted_output.render`

```python
render(filepath: str) -> str:
```

Fetch/parse/render docstrings (simple wrapper function to allow decorators).

**Parameters:**

- `filepath` \[`str`\]: Path to the `Python` module to be processed.

**Returns:**

- \[`str`\]: The `Markdown` as outputted by `astdocs`.

**Decoration** via `@astdocs.postrender(lint)`.

# Module `object_graph`

Prepare an output to visualize the dependency graph of a module/package.

Visualization is intended to be generated via [`D3.js`](https://d3js.org/). See the
~~code in this folder, or refer to the~~ example by the creator of the library himself
[there](https://observablehq.com/@d3/force-directed-graph).

**Notes:**

One can abuse the example at the page linked above: replace the data (browse a bit, find
the right cell, click on the small paperclip icon). If the nodes are flying all over
when applying the forces on the graph data, try to modify the parameters of the
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

**Known problems:**

This small toy thing breaks on `from ... import *` statements (cannot guess which
objects are imported; but this is bad `Python` habits anyhow).

**Functions:**

- [`is_local()`](#object_graphis_local)
- [`add_node()`](#object_graphadd_node)
- [`add_edge()`](#object_graphadd_edge)
- [`graph()`](#object_graphgraph)

## Functions

### `object_graph.is_local`

```python
is_local(o: str, objects: typing.List[str]) -> bool:
```

Check whether an object is local, or external, looking at its path.

**Parameters:**

- `o` \[`str`\]: String representation of the object path.
- `objects` \[`typing.List[str]`\]: List of local objects to check for.

**Returns:**

- \[`bool`\]: Whether the object is local or external to the `Python` parsed package(s).

### `object_graph.add_node`

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

### `object_graph.add_edge`

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

### `object_graph.graph`

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

# Module `to_html`

Render the output in `HTML`

Includes syntax highlighting (and code blocks), anchor links, minified `HTML` output.

**Requirements:**

- [`markdown`](https://github.com/Python-Markdown/markdown)
- [`minify-html`](https://github.com/wilsonzlin/minify-html)
- [`pygments`](https://pygments.org/)

**Notes:**

The CSS for the syntax highlighting can be generated using:

```shell
$ pygmentize -S default -f html -a .codehilite > html/pygments.css
```

check the list of available styles with `pygmentize -L`.

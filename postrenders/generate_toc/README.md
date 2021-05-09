# Module `process`

Generate a table of contents from all listed objects.

Note this example should be run with:

```shell
$ ASTDOCS_SPLIT_BY=m python3 process.py | csplit -qz - '/^%%%BEGIN/' '{*}'
$ grep -v '^%%%BEGIN' xx00 > README.md
$ rm xx00
> for f in xx??; do
>   path=$(grep -m1 '^%%%BEGIN' $f | sed -r 's|%%%.* (.*)|\1|g;s|\.|/|g')
>   mkdir -p "docs/$(dirname $path)"
>   grep -v '^%%%BEGIN' $f > "docs/$path.md"  # double quotes are needed
>   rm $f
> done
```

(See `process.sh` in this directory.)

**Functions:**

- [`toc()`](#processtoc)

## Functions

### `process.toc`

```python
toc(
    objects: typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]], 
    path_prefix: str,
) -> str:
```

Filter all objects and generate the table of content.

**Parameters:**

- `objects` \[`typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]]`\]: Dictionary of
  objects encountered in all modules parsed by `astdocs`.
- `path_prefix` \[`str`\]: Extra bits to add to the path.

**Returns:**

- \[`str`\]: `Markdown`-formatted table of content.

**Notes:**

In this example we are excluding the documentation of the `astdocs` module itself to be
rendered. This part can be removed to generalise the function.

# Table of Contents

As an example, below all \[sub\]modules in the `postrenders` directory:

- Module [`generate_toc.process`](docs/generate_toc/process.md)
  - Function
    [`generate_toc.process.toc`](docs/generate_toc/process.md#generate_tocprocesstoc)
- Module [`linted_output.process`](docs/linted_output/process.md)
  - Function
    [`linted_output.process.lint`](docs/linted_output/process.md#linted_outputprocesslint)
  - Function
    [`linted_output.process.render`](docs/linted_output/process.md#linted_outputprocessrender)
- Module [`object_graph.process`](docs/object_graph/process.md)
  - Function
    [`object_graph.process.is_local`](docs/object_graph/process.md#object_graphprocessis_local)
  - Function
    [`object_graph.process.add_node`](docs/object_graph/process.md#object_graphprocessadd_node)
  - Function
    [`object_graph.process.add_edge`](docs/object_graph/process.md#object_graphprocessadd_edge)
  - Function
    [`object_graph.process.graph`](docs/object_graph/process.md#object_graphprocessgraph)
- Module [`to_html.process`](docs/to_html/process.md)

# Module `generate_toc.process`

Generate a table of contents from all listed objects.

Note this example should be run with:

```shell
$ ASTDOCS_SPLIT_BY=m python3 process.py | csplit -qz - '/^%%%BEGIN/' '{*}'
$ sed '1d' xx00 > README.md
$ rm xx00
> for f in xx??; do
>   path=$(grep -m1 '^%%%BEGIN' $f | sed -r 's|%%%.* (.*)|\1|g;s|\.|/|g')
>   mkdir -p "docs/$(dirname $path)"
>   sed '1d' $f > "docs/$path.md"  # double quotes are needed
>   rm $f
> done
```

(See `process.sh` in this directory.)

**Functions:**

- [`toc()`](#generate_tocprocesstoc)

## Functions

### `generate_toc.process.toc`

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

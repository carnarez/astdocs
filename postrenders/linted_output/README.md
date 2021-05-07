# Module `process`

Pipe the output of `astdocs` to a linter.

As any other strictly-defined syntax, `Markdown` can (should?) be linted. This small
post-rendering does just that. (This will not be integrated to `astdocs` as it adds a
dependency, which is **out of scope**.)

The `Python` linter chosen for this example is
[`Mdformat`](https://github.com/executablebooks/mdformat), code style described
[there](https://mdformat.readthedocs.io/en/stable/users/style.html).

**Functions:**

- [`lint()`](#processlint)
- [`render()`](#processrender)

## Functions

### `process.lint`

```python
lint(md: str) -> str:
```

Lint the `Markdown`.

**Parameters:**

- `md` \[`str`\]: The `Markdown` as outputted by `astdocs`.

**Returns:**

- \[`str`\]: Linted `Markdown`.

### `process.render`

```python
render(filepath: str) -> str:
```

Fetch/parse/render docstrings (simple wrapper function to allow decorators).

**Parameters:**

- `filepath` \[`str`\]: Path to the `Python` module to be processed

**Returns:**

- \[`str`\]: The `Markdown` as outputted by `astdocs`.

**Decoration** via `@astdocs.postrender(lint)`.

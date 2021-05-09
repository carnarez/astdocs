r"""Generate a table of contents from all listed objects.

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
"""

import os
import typing

import astdocs

cwd = os.getcwd()


def toc(
    objects: typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]],
    path_prefix: str = ".",
) -> str:
    """Filter all objects and generate the table of content.

    Parameters
    ----------
    objects : typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]]
        Dictionary of objects encountered in all modules parsed by `astdocs`.
    path_prefix : str
        Extra bits to add to the path.

    Returns
    -------
    : str
        `Markdown`-formatted table of content.

    Notes
    -----
    In this example we are excluding the documentation of the `astdocs` module itself to
    be rendered. This part can be removed to generalise the function.
    """
    md = ""

    if not len(path_prefix):
        path_prefix = "."

    for m in objects:
        name = m.split(".")[-1]
        if name != "astdocs":  # just for this example
            path = m.replace(".", "/")
            md += f"\n- Module [`{m}`]({path_prefix}/{path}.md)"
            for t in ["functions", "classes"]:
                for o in objects[m][t]:
                    anchor = m.replace(".", "") + o.replace(".", "")  # github
                    md += (
                        f'\n    - {t.capitalize().rstrip("es")} '
                        f"[`{m}.{o}`]({path_prefix}/{path}.md#{anchor})"
                    )

    return md


md_doc = astdocs.render_recursively(f"{cwd}/..", cwd)  # parent folder
md_toc = toc(astdocs._objects, "docs")

print(
    "%%%BEGIN TOC\n"
    "# Table of Contents\n\n"
    f'As an example, below all [sub]modules in the `{cwd.split("/")[-2]}` directory:'
)
print(md_toc)
print(md_doc)

"""Generate a table of contents from listed objects.

Requirements
------------
* `astdocs`
"""

import typing

import astdocs


def generate_toc(
    objects: typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]]
) -> str:
    """Filter objects and generate the table of content.

    Parameters
    ----------
    objects : typing.Dict[str, typing.Dict[str, typing.Dict[str, str]]]
        Dictionary of objects encountered in all modules parsed by `astdocs`.

    Returns
    -------
    : str
        `Markdown`-formatted table of content.
    """
    md = ""

    for m in objects:
        anchor = m.replace(".", "")  # github
        md += f"\n- [`{m}`](#{anchor})"
        for t in ["functions", "classes"]:
            for o in objects[m][t]:
                anchor = (m + o).replace(".", "")  # github
                md += f"\n    - [`{m}.{o}`](#{anchor})"

    return md


md_doc = astdocs.render_recursively(".")
md_toc = generate_toc(astdocs.objects)

print(f"{md_toc}\n\n{md_doc}")

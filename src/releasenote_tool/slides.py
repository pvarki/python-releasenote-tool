"""Marp slide deck rendered from the user-facing changes of a release."""

import re

from .notes import Change, slug

FRONT_MATTER = "---\nmarp: true\npaginate: true\n---"
SEPARATOR = "\n\n---\n\n"

RULE_RE = re.compile(r" {0,3}(?:-{3,}|\*{3,}|_{3,})\s*")

# Lines that open a block of their own, and so never join the line above them.
LIST_RE = re.compile(r"\s*(?:[-*+]|\d+[.)])\s")
BLOCK_RE = re.compile(r"\s*(?:#{1,6}\s|>|\||```|!\[|<)")

# A change whose body runs longer than this is rendered by the theme at a smaller size.
DENSE_LINES = 12


def rules(body: str) -> str:
    """Thematic breaks inside a change turned into plain HTML, so they cannot split its slide.

    A rule directly under text is a setext heading rather than a break, and is left alone.
    """
    lines = body.split("\n")
    kept = []
    for index, line in enumerate(lines):
        heading = index and lines[index - 1].strip()
        kept.append("<hr />" if RULE_RE.fullmatch(line) and not heading else line)
    return "\n".join(kept)


def own_line(line: str) -> bool:
    """True for a line that opens a block of its own and so joins neither neighbour."""
    return bool(BLOCK_RE.match(line) or RULE_RE.fullmatch(line))


def unwrap(body: str) -> str:
    """Soft-wrapped prose joined back into one line per paragraph or bullet.

    Marp renders a single newline as a line break, so the wrapping of a pull request body would
    otherwise break sentences mid-slide. Headings, images, rules, tables and fenced code keep
    their own lines.
    """
    joined: list[str] = []
    fenced = False
    for line in body.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            joined.append(line)
            continue
        above = joined[-1] if joined else ""
        wraps = (
            not fenced
            and line.strip()
            and above.strip()
            and not LIST_RE.match(line)
            and not own_line(line)
            and (LIST_RE.match(above) or not own_line(above))
            # Two trailing spaces or a backslash is a line break someone asked for.
            and not above.endswith(("  ", "\\"))
        )
        if wraps:
            joined[-1] = f"{above.rstrip()} {line.strip()}"
        else:
            joined.append(line)
    return "\n".join(joined)


def directives(change: Change, dense: bool) -> str:
    """Per-slide Marp directives: the pull request as a footer, the size class when needed."""
    lines = ["_class: dense"] if dense else []
    lines.append(f'_footer: "[#{change.number}]({change.url})"')
    return "<!--\n" + "\n".join(lines) + "\n-->"


def slide(change: Change) -> str:
    body = unwrap(rules(change.body))
    dense = body.count("\n") + 1 > DENSE_LINES
    heading = f"{directives(change, dense)}\n\n### {change.title}"
    return f"{heading}\n\n{body}" if body else heading


def title(version: str, date: str, url: str | None) -> str:
    """The opening slide: the repository over the version it is being released as."""
    heading = f"# {slug(url)}\n\n## {version} — {date}" if url else f"# {version}\n\n## {date}"
    return f"<!-- _class: title -->\n\n{heading}"


def render(changes: list[Change], version: str, date: str, url: str | None = None) -> str:
    deck = [title(version, date, url)] + [slide(change) for change in changes]
    return f"{FRONT_MATTER}\n\n" + SEPARATOR.join(deck) + "\n"

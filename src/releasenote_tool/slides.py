"""Marp slide deck rendered from the user-facing changes of a release."""

import re

from .notes import Change, slug

FRONT_MATTER = "---\nmarp: true\npaginate: true\n---"
SEPARATOR = "\n\n---\n\n"

RULE_RE = re.compile(r" {0,3}(?:-{3,}|\*{3,}|_{3,})\s*")

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


def directives(change: Change, dense: bool) -> str:
    """Per-slide Marp directives: the pull request as a footer, the size class when needed."""
    lines = ["_class: dense"] if dense else []
    lines.append(f'_footer: "[#{change.number}]({change.url})"')
    return "<!--\n" + "\n".join(lines) + "\n-->"


def slide(change: Change) -> str:
    body = rules(change.body)
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

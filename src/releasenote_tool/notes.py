"""User-facing release notes assembled from the pull requests in a git tag range."""

import json
import re
import subprocess  # nosec B404
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import click

# The user-facing section of the pull request template, one ### per change:
#
#     <!-- releasenote:start -->
#     ### Short title of the change
#     A few sentences describing the change to a user.
#     <!-- releasenote:end -->
#
# A block left unterminated ends at the next ## heading instead of swallowing the rest of the body.
BLOCK_RE = re.compile(
    r"<!--\s*releasenote:start\s*-->(?P<block>.*?)(?=<!--\s*releasenote:end\s*-->|^## |\Z)",
    re.DOTALL | re.MULTILINE,
)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
ENTRY_RE = re.compile(r"^### +(?P<title>.+?)\s*$", re.MULTILINE)
PLACEHOLDER = frozenset(
    {"short title of the change", "a few sentences describing the change to a user."}
)


@dataclass(frozen=True)
class Change:
    """One user-facing change: one ### in the release notes, later one slide."""

    title: str
    body: str
    number: int
    url: str

    def markdown(self) -> str:
        heading = f"### {self.title} ([#{self.number}]({self.url}))"
        return f"{heading}\n\n{self.body}" if self.body else heading


def filled(title: str, body: str) -> bool:
    """False for an entry left as the placeholder the pull request template ships with."""
    return title.strip().lower() not in PLACEHOLDER and body.strip().lower() not in PLACEHOLDER


def entries(body: str) -> list[tuple[str, str]]:
    """Title and body of every ### inside the release note markers of a pull request body.

    Text above the first ### is dropped; only headed entries are published.
    """
    found = []
    for marked in BLOCK_RE.finditer(body):
        block = COMMENT_RE.sub("", marked["block"])
        headings = list(ENTRY_RE.finditer(block))
        ends = [heading.start() for heading in headings[1:]] + [len(block)]
        for heading, end in zip(headings, ends):
            text = block[heading.end() : end].strip()
            if filled(heading["title"], text):
                found.append((heading["title"].strip(), text))
    return found


def changes(pull_request: dict[str, Any]) -> list[Change]:
    """Every user-facing change a pull request contributes, in the order it lists them."""
    number, url = pull_request["number"], pull_request["url"]
    return [Change(title, body, number, url) for title, body in entries(pull_request["body"] or "")]


def slug(url: str) -> str:
    """owner/repo out of a repository URL."""
    return url.rstrip("/").split("/", 3)[-1]


def _gh(*args: str) -> Any:
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)  # nosec
    if result.returncode:
        raise click.ClickException(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def window(since: str | None, until: str) -> str:
    """GitHub search window for a tag range, with the start tag's own merge left out."""
    if not since:
        return f"<={until}"
    return f"{(datetime.fromisoformat(since) + timedelta(seconds=1)).isoformat()}..{until}"


def pull_requests(repo: str, since: str | None, until: str) -> list[dict[str, Any]]:
    """Merged pull requests in the range's time window, newest first. `repo` is owner/repo."""
    return _gh(  # type: ignore[no-any-return]
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "merged",
        "--limit",
        "200",
        "--search",
        f"merged:{window(since, until)}",
        "--json",
        "number,title,body,url",
    )


def render(changes: list[Change], version: str, date: str) -> str:
    blocks = [change.markdown() for change in changes]
    return f"## {version} ({date})\n\n" + "\n\n".join(blocks) + "\n"

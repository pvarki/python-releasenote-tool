"""User-facing release notes assembled from the pull requests in a git tag range."""

import json
import re
import subprocess  # nosec B404
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any

import click

from .changelog import Commit

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


def commits(pull_request: dict[str, Any]) -> list[Commit]:
    """The conventional commits a pull request carries, newest first like `git log`.

    Only needed for a pull request the range does not already contain, which is why
    `pull_requests` does not ask for them.
    """
    entries = reversed(pull_request.get("commits", []))
    parsed = (
        Commit.parse(entry["oid"], entry["messageHeadline"], entry["messageBody"])
        for entry in entries
    )
    return [commit for commit in parsed if commit]


def slug(url: str) -> str:
    """owner/repo out of a repository URL."""
    return url.rstrip("/").split("/", 3)[-1]


MISSING = "gh is not on PATH. Install the GitHub CLI, or run this from the tool's container image."


def _gh(*args: str) -> Any:
    try:
        result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)  # nosec
    except FileNotFoundError as absent:
        raise click.ClickException(MISSING) from absent
    if result.returncode:
        raise click.ClickException(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


# Commits per GraphQL query
BATCH = 100
FIELDS = ("number", "title", "body", "url")
ASSOCIATED = (
    "associatedPullRequests(first: 5) "
    "{ nodes { number title body url mergedAt repository { nameWithOwner } } }"
)


def _query(shas: Sequence[str]) -> str:
    """One query asking which pull requests each sha belongs to."""
    lookups = " ".join(
        f'c{index}: object(oid: "{sha}") {{ ... on Commit {{ {ASSOCIATED} }} }}'
        for index, sha in enumerate(shas)
    )
    return (
        "query($owner: String!, $name: String!) "
        f"{{ repository(owner: $owner, name: $name) {{ {lookups} }} }}"
    )


def _associated(repo: str, shas: Sequence[str]) -> Iterator[dict[str, Any]]:
    owner, name = repo.split("/", 1)
    found = _gh(
        "api",
        "graphql",
        "-f",
        f"query={_query(shas)}",
        "-F",
        f"owner={owner}",
        "-F",
        f"name={name}",
    )
    for commit in found["data"]["repository"].values():
        if commit:  # A sha GitHub does not know comes back null.
            yield from commit["associatedPullRequests"]["nodes"]


def pull_requests(repo: str, shas: Sequence[str]) -> list[dict[str, Any]]:
    """Merged pull requests the range's commits belong to, newest first. `repo` is owner/repo."""
    found: dict[int, dict[str, Any]] = {}
    for batch in range(0, len(shas), BATCH):
        for pull in _associated(repo, shas[batch : batch + BATCH]):
            if pull["mergedAt"] and pull["repository"]["nameWithOwner"] == repo:
                found.setdefault(pull["number"], {field: pull[field] for field in FIELDS})
    return list(found.values())


def pull_request(repo: str, number: int) -> dict[str, Any]:
    """One pull request by number, merged or not. `repo` is owner/repo."""
    return _gh(  # type: ignore[no-any-return]
        "pr", "view", str(number), "--repo", repo, "--json", "number,title,body,url,commits"
    )


def render(changes: list[Change], version: str, date: str) -> str:
    blocks = [change.markdown() for change in changes]
    return f"## {version} ({date})\n\n" + "\n\n".join(blocks) + "\n"

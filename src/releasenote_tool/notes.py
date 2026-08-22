"""User-facing release notes assembled from the pull requests in a git tag range."""

import json
import re
import subprocess  # nosec B404
from datetime import datetime, timedelta
from typing import Any

import click

HEADING_RE = re.compile(r"^#{1,4}\s*User[- ]Facing.*$", re.IGNORECASE | re.MULTILINE)
NEXT_HEADING_RE = re.compile(r"^#{1,2}\s", re.MULTILINE)


def user_facing(body: str) -> str | None:
    """The User-Facing Summary section of a pull request body, or None if it was left out."""
    heading = HEADING_RE.search(body)
    if not heading:
        return None
    return NEXT_HEADING_RE.split(body[heading.end() :], maxsplit=1)[0].strip() or None


def block(pull_request: dict[str, Any]) -> str | None:
    """One release note block, under a heading naming the pull request it came from."""
    text = user_facing(pull_request["body"] or "")
    if not text:
        return None
    number, url = pull_request["number"], pull_request["url"]
    return f"### {pull_request['title']} ([#{number}]({url}))\n\n{text}"


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


def render(blocks: list[str], version: str, date: str) -> str:
    return f"## {version} ({date})\n\n" + "\n\n".join(blocks) + "\n"

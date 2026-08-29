import pathlib
from collections.abc import Callable
from typing import Any

import click

from . import notes
from .changelog import (
    Commit,
    commits_in_range,
    date_of,
    origin_url,
    previous_tag,
    render,
    sections,
    timestamp_of,
)

RANGE_OPTIONS = [
    click.option("--repo", default=".", help="Repository to read commits from."),
    click.option(
        "--from", "start", help="Start of the range, exclusive. Defaults to the previous tag."
    ),
    click.option("--to", "end", default="HEAD", help="End of the range, inclusive."),
    click.option("--out", type=click.Path(path_type=pathlib.Path), help="Directory to write into."),
    click.option("--url", help="Repository URL to link to. Defaults to the origin remote."),
]


def range_options(command: Callable[..., Any]) -> Callable[..., Any]:
    for option in reversed(RANGE_OPTIONS):
        command = option(command)
    return command


def documents(
    commits: list[Commit],
    changes: list[notes.Change],
    version: str,
    date: str,
    url: str | None,
) -> dict[str, str]:
    """The markdown files a build produces, by filename.

    A range whose pull requests carry no user-facing changes gets the changelog alone.
    """
    files = {"changelog.md": render(commits, version, date, url)}
    if changes:
        files["release-notes.md"] = notes.render(changes, version, date)
        files["release-body.md"] = (
            f"{files['release-notes.md']}\n## Changelog\n\n{sections(commits, url)}"
        )
    else:
        files["release-body.md"] = files["changelog.md"]
    return files


@click.group()
def main() -> None:
    """Generate changelogs / release notes from a git tag range."""


@main.command()
@range_options
def changelog(
    repo: str, start: str | None, end: str, out: pathlib.Path | None, url: str | None
) -> None:
    """Technical changelog from the conventional commits in a tag range."""
    commits = commits_in_range(repo, start or previous_tag(repo, end), end)
    markdown = render(commits, end, date_of(repo, end), url or origin_url(repo))
    if out is None:
        click.echo(markdown, nl=False)
        return
    out.mkdir(parents=True, exist_ok=True)
    (out / "changelog.md").write_text(markdown)


@main.command()
@range_options
def build(
    repo: str, start: str | None, end: str, out: pathlib.Path | None, url: str | None
) -> None:
    """Release notes from the pull requests in a tag range, with the changelog below."""
    start = start or previous_tag(repo, end)
    url = url or origin_url(repo)
    if not url:
        raise click.ClickException("No origin remote to read pull requests from, pass --url.")
    date = date_of(repo, end)
    commits = commits_in_range(repo, start, end)
    since = timestamp_of(repo, start) if start else None
    pulls = notes.pull_requests(notes.slug(url), since, timestamp_of(repo, end))
    changes = [change for pull in pulls for change in notes.changes(pull)]

    files = documents(commits, changes, end, date, url)
    if out is None:
        click.echo(files["release-body.md"], nl=False)
        return
    out.mkdir(parents=True, exist_ok=True)
    for name, markdown in files.items():
        (out / name).write_text(markdown)

import pathlib
from collections.abc import Callable
from typing import Any

import click

from . import assets, export, notes, slides
from .changelog import (
    Commit,
    commits_in_range,
    date_of,
    origin_url,
    previous_tag,
    render,
    require_clone,
    sections,
    timestamp_of,
)

RANGE_OPTIONS = [
    click.option("--repo", default=".", help="Path to the local clone to read commits from."),
    click.option(
        "--from", "start", help="Start of the range, exclusive. Defaults to the previous tag."
    ),
    click.option("--to", "end", default="HEAD", help="End of the range, inclusive."),
    click.option(
        "--product", help="Name the files lead with. Defaults to the origin repository's."
    ),
    click.option("--release", help="Version the documents claim. Defaults to --to."),
    click.option("--out", type=click.Path(path_type=pathlib.Path), help="Directory to write into."),
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
    """The markdown files one run produces, by kind.

    A range whose pull requests carry no user-facing changes gets the changelog alone.
    """
    files = {"changelog": render(commits, version, date, url)}
    if changes:
        files["release-notes"] = notes.render(changes, version, date)
        files["release-body"] = (
            f"{files['release-notes']}\n## Changelog\n\n{sections(commits, url)}"
        )
        files["slides"] = slides.render(changes, version, date, url)
    else:
        files["release-body"] = files["changelog"]
    return files


@click.group()
def main() -> None:
    """Generate changelogs / release notes from a git tag range."""


@main.command("commits")
@range_options
def commits_command(
    repo: str,
    start: str | None,
    end: str,
    product: str | None,
    release: str | None,
    out: pathlib.Path | None,
) -> None:
    """Technical changelog from the conventional commits in a tag range."""
    require_clone(repo)
    url = origin_url(repo)
    label = release or end
    commits = commits_in_range(repo, start or previous_tag(repo, end), end)
    markdown = render(commits, label, date_of(repo, end), url)
    if out is None:
        click.echo(markdown, nl=False)
        return
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{assets.project(repo, url, product)}-{assets.version(label)}"
    (out / assets.names(stem)["changelog"]).write_text(markdown)


@main.command("changes")
@range_options
@click.option(
    "--slides",
    "formats",
    type=click.Choice(export.FORMATS),
    multiple=True,
    help="Also render the deck in this format. Repeatable, needs --out.",
)
@click.option(
    "--pr", type=int, help="Also read this pull request, merged or not. For previewing an open one."
)
def changes_command(
    repo: str,
    start: str | None,
    end: str,
    product: str | None,
    release: str | None,
    out: pathlib.Path | None,
    formats: tuple[str, ...],
    pr: int | None,
) -> None:
    """Release notes from the pull requests in a tag range, with the changelog below."""
    if formats and out is None:
        raise click.ClickException("--slides has nowhere to write, pass --out.")
    require_clone(repo)
    start = start or previous_tag(repo, end)
    url = origin_url(repo)
    if not url:
        raise click.ClickException(
            f"{repo} has no origin remote, so there is no repository to read pull requests from."
        )
    date = date_of(repo, end)
    commits = commits_in_range(repo, start, end)
    since = timestamp_of(repo, start) if start else None
    slug = notes.slug(url)
    pulls = notes.pull_requests(slug, since, timestamp_of(repo, end))
    if pr is not None and not any(pull["number"] == pr for pull in pulls):
        preview = notes.pull_request(slug, pr)
        pulls = [preview, *pulls]
        seen = {commit.sha for commit in commits}
        commits = [*(c for c in notes.commits(preview) if c.sha not in seen), *commits]
    changes = [change for pull in pulls for change in notes.changes(pull)]

    label = release or end
    files = documents(commits, changes, label, date, url)
    if out is None:
        click.echo(files["release-body"], nl=False)
        return
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{assets.project(repo, url, product)}-{assets.version(label)}"
    filenames = assets.names(stem)
    for kind, markdown in files.items():
        (out / filenames[kind]).write_text(markdown)

    deck = out / filenames["slides"]
    if formats and not deck.exists():
        click.echo("No user-facing changes in the range, no slides to render.", err=True)
        return
    for fmt in formats:
        export.run(deck, out / assets.rendered(stem, fmt))


@main.command("slides")
@click.argument("deck", type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path))
@click.option(
    "--format",
    "formats",
    type=click.Choice(export.FORMATS),
    multiple=True,
    default=("pdf",),
    help="Format to render. Repeatable.",
)
@click.option(
    "--out",
    type=click.Path(path_type=pathlib.Path),
    help="Directory to write into. Defaults to the deck's own.",
)
def slides_command(deck: pathlib.Path, formats: tuple[str, ...], out: pathlib.Path | None) -> None:
    """Render an existing deck, without going near git or GitHub."""
    if out:
        out.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        export.run(deck, export.target(deck, fmt, out))

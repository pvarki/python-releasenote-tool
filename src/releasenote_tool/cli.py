import pathlib

import click

from .changelog import commits_in_range, date_of, origin_url, previous_tag, render


@click.group()
def main() -> None:
    """Generate changelogs / release notes from a git tag range."""


@main.command()
@click.option("--repo", default=".", help="Repository to read commits from.")
@click.option(
    "--from", "start", help="Start of the range, exclusive. Defaults to the previous tag."
)
@click.option("--to", "end", default="HEAD", help="End of the range, inclusive.")
@click.option("--out", type=click.Path(path_type=pathlib.Path), help="Write <out>/changelog.md.")
@click.option("--url", help="Repository URL commits link to. Defaults to the origin remote.")
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

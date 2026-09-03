"""The changelog command against a real repository: the walk, the tags and the origin remote."""

import os
import re
import subprocess

import pytest
from click.testing import CliRunner
from conftest import REPO

from releasenote_tool.changelog import Commit, previous_tag
from releasenote_tool.cli import main

TERN = (
    "An arctic tern flies pole to pole every year, the longest migration there is.\n\n"
    "The map drew that as one marker per sighting.\n"
)
PIGEON = (
    "A homing pigeon finds its loft from a thousand kilometres away.\n\n"
    "The map could not find the sighting you logged a minute ago.\n"
)
PENGUINS = "Emperor penguins arrive in the thousands, so an unfiltered list is unreadable.\n"
OTTERS = "Sea otters hold hands while they sleep so they do not drift apart.\n\nRefs: #118\n"
BEES = "Honeybees can recognise human faces. This commit recognises nothing.\n"
MAYFLY = (
    "A field token lasted about as long as a mayfly, which is one day.\n\n"
    "BREAKING CHANGE: tokens issued before v1.1 no longer authenticate.\n"
)
HIVE = "A queenless hive turns loud and starts raising drones.\n"

HISTORY = [
    ("chore: project scaffolding", ""),
    ("feat(map): draw migration routes as one line", TERN),
    ("fix: centre the map on the last sighting", PIGEON),
    ("feat(sightings): filter by species", PENGUINS),
    ("fxi(otters): keep a resting pair on one marker", OTTERS),
    ("wip", BEES),
    ("refactor(auth): rework the field tokens", MAYFLY),
]
RELEASED = 3
TOPIC = ("fix(hives): call out a queenless hive", HIVE)
MERGE = "chore: merge the queenless hives branch"
LINK_RE = re.compile(rf"{re.escape(REPO)}/commit/([0-9a-f]+)\)")

ENV = {
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.com",
    "GIT_COMMITTER_NAME": "Fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.com",
}


def git(path, *args, minute=0):
    when = f"2026-08-01T12:{minute:02d}:00+00:00"
    env = {**os.environ, **ENV, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    return subprocess.run(  # nosec
        ["git", "-C", str(path), *args], check=True, capture_output=True, text=True, env=env
    ).stdout


def commit(path, subject, body, minute):
    message = ["-m", subject] + (["-m", body] if body else [])
    git(path, "commit", "-q", "--allow-empty", *message, minute=minute)


def walk(path, *revs):
    """What git log hands the tool: (sha, subject) per commit, merges dropped."""
    log = git(path, "log", "--no-merges", "--format=%H %s", *revs)
    return [line.split(" ", 1) for line in log.splitlines()]


def conventional(entries):
    """The shas of the walked commits the parser accepts."""
    return {sha for sha, subject in entries if Commit.parse(sha, subject, "")}


def linked(markdown):
    """The shas a rendered changelog links, which only match once origin_url rewrote the remote."""
    return set(LINK_RE.findall(markdown))


@pytest.fixture
def repo(tmp_path):
    """HISTORY as a repository: v1.0.0 after the first RELEASED commits, v1.1.0 on a merge."""
    path = tmp_path / "repo"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    git(path, "remote", "add", "origin", "git@example.com:example/test.git")
    for minute, (subject, body) in enumerate(HISTORY):
        commit(path, subject, body, minute)
        if minute == RELEASED - 1:
            git(path, "tag", "v1.0.0")
    git(path, "checkout", "-q", "-b", "topic")
    commit(path, *TOPIC, minute=len(HISTORY))
    git(path, "checkout", "-q", "main")
    git(path, "merge", "-q", "--no-ff", "-m", MERGE, "topic", minute=len(HISTORY) + 1)
    git(path, "tag", "v1.1.0")
    return path


@pytest.fixture
def changelog(repo, tmp_path):
    """The changelog command over the fixture repository, returning what it wrote."""

    def run(*args):
        out = tmp_path / "out"
        result = CliRunner().invoke(
            main, ["changelog", "--repo", str(repo), "--out", str(out), *args]
        )
        assert result.exit_code == 0, result.output
        return (out / "changelog.md").read_text()

    return run


def test_the_range_is_the_conventional_commits_since_the_previous_tag(repo, changelog):
    markdown = changelog("--to", "v1.1.0")
    entries = walk(repo, "v1.0.0..v1.1.0")

    assert markdown.splitlines()[0] == "## v1.1.0 (2026-08-01)"
    assert 0 < len(conventional(entries)) < len(entries)
    assert linked(markdown) == conventional(entries)
    assert git(repo, "rev-parse", "v1.1.0").strip() not in linked(markdown)


def test_a_commit_body_never_reaches_the_changelog(changelog):
    markdown = changelog("--to", "v1.1.0")

    for _, body in [*HISTORY, TOPIC]:
        assert not body or body.splitlines()[0] not in markdown


def test_a_breaking_footer_in_the_body_lands_under_breaking_changes(repo, changelog):
    markdown = changelog("--to", "v1.1.0")
    sha = git(repo, "log", "-1", "--format=%H", "--grep", "BREAKING CHANGE:").strip()

    assert linked(markdown.split("### ")[1]) == {sha}


def test_the_first_release_takes_the_whole_history(repo, changelog):
    assert previous_tag(str(repo), "v1.0.0") is None

    markdown = changelog("--to", "v1.0.0")

    assert markdown.splitlines()[0] == "## v1.0.0 (2026-08-01)"
    assert linked(markdown) == conventional(walk(repo, "v1.0.0"))

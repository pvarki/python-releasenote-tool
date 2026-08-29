"""Pull request bodies from tests/data, for the parsing and rendering tests."""

import pathlib

import pytest

DATA = pathlib.Path(__file__).parent / "data"
REPO = "https://example.com/example/test"

# The pull requests tests/data/pulls holds a body for, in the order they merged.
PULLS = {
    "otters": (118, "fix: keep otter pairs on one marker"),
    "no-section": (119, "revert: tile prefetch"),
    "bees": (120, "feat: hive health cards"),
    "wombats": (121, "feat: classify scat photos"),
    "placeholder": (122, "refactor: rename the tile cache"),
    "narwhals": (123, "feat: tusk measurements"),
    "flamingos": (124, "feat: plumage colour scale"),
    "headless": (125, "chore: tidy the empty states"),
    "subheadings": (126, "feat: tracker settings in the sidebar"),
    "comments-left-in": (127, "feat: night mode for field work"),
    "empty-block": (128, "chore: bump the tile dependency"),
    "unterminated": (129, "feat: migration route overlay"),
    "placeholder-plus-real": (131, "feat: colony size estimate"),
}


def _pull_request(name):
    number, title = PULLS[name]
    return {
        "body": (DATA / "pulls" / f"{name}.md").read_text(),
        "number": number,
        "title": title,
        "url": f"{REPO}/pull/{number}",
    }


@pytest.fixture
def pull():
    """One fixture pull request by name, shaped like a `gh pr list` entry."""
    return _pull_request


@pytest.fixture
def pulls():
    """Every fixture pull request, newest first, the order `gh pr list` returns them in."""
    return [_pull_request(name) for name in reversed(PULLS)]


@pytest.fixture
def original_datadir():
    """Where pytest-regressions keeps the rendered output it checks against."""
    return DATA / "expected"

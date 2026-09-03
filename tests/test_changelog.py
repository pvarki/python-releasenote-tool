import pytest

from releasenote_tool.changelog import SECTIONS, TYPES, Commit, render

LOG = [
    ("aaaaaaaaaa", "feat(cli): add changelog command", ""),
    ("bbbbbbbbbb", "fix: handle an empty tag range", ""),
    ("cccccccccc", "chore(ci): pin prek action", ""),
    ("dddddddddd", "feat!: drop python 3.10", ""),
    ("eeeeeeeeee", "refactor(auth): rework tokens", "BREAKING CHANGE: tokens now expire"),
    ("ffffffffff", "Merge pull request #12 from foo", ""),
    ("9999999999", "wip", ""),
]


def test_render_groups_and_drops_non_conventional():
    commits = [c for c in (Commit.parse(*entry) for entry in LOG) if c]
    md = render(commits, "v1.1.0", "2026-08-22", "https://example.com/example/test")

    assert md.splitlines()[0] == "## v1.1.0 (2026-08-22)"
    assert [line for line in md.splitlines() if line.startswith("### ")] == [
        "### Breaking changes",
        "### Features",
        "### Fixes",
        "### Other changes",
    ]
    assert md.count("rework tokens") == 1
    assert "Merge pull request" not in md
    assert "wip" not in md
    assert (
        "- **cli:** add changelog command "
        "([aaaaaaa](https://example.com/example/test/commit/aaaaaaaaaa))"
    ) in md


def test_render_without_a_url_falls_back_to_the_short_sha():
    commit = Commit.parse("dddddddddd", "feat!: drop python 3.10", "")
    assert "- drop python 3.10 (ddddddd)" in render([commit], "v1.1.0", "2026-08-22")


def test_empty_range():
    assert "_No notable changes._" in render([], "v1.1.0", "2026-08-22")


@pytest.mark.parametrize(
    ("subject", "body"),
    [
        ("fxi: rotate tokens", ""),
        ("deps: bump click", ""),
        ("feta(map): plot the routes", ""),
        ("fxi!: drop v1", ""),
        ("fxi: drop v1", "BREAKING CHANGE: the v1 feed is gone"),
    ],
    ids=lambda value: value or "no body",
)
def test_a_type_outside_the_set_is_dropped(subject, body):
    assert Commit.parse("aaaaaaaaaa", subject, body) is None


@pytest.mark.parametrize("type_", sorted(TYPES))
def test_every_conventional_type_parses(type_):
    commit = Commit.parse("aaaaaaaaaa", f"{type_}(scope): describe it", "")
    assert commit is not None
    assert commit.section == (type_ if type_ in ("feat", "fix") else "other")
    assert commit.section in SECTIONS


@pytest.mark.parametrize(
    ("subject", "section", "scope"),
    [("Feat: capitalised type", "feat", None), ("FIX(Map): shouted", "fix", "Map")],
)
def test_a_type_is_matched_case_insensitively_and_the_scope_kept(subject, section, scope):
    commit = Commit.parse("aaaaaaaaaa", subject, "")
    assert commit is not None
    assert (commit.section, commit.scope) == (section, scope)


def test_a_dropped_commit_leaves_nothing_behind():
    log = [
        ("aaaaaaaaaa", "feat: add hive health cards", ""),
        ("bbbbbbbbbb", "fxi: rotate the field tokens", "BREAKING CHANGE: tokens now expire"),
    ]
    md = render([c for c in (Commit.parse(*entry) for entry in log) if c], "v1.1.0", "2026-08-22")

    assert "rotate the field tokens" not in md
    assert "tokens now expire" not in md
    assert "### Breaking changes" not in md
    assert md.count("\n- ") == 1

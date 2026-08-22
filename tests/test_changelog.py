from releasenote_tool.changelog import Commit, render

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
    md = render(commits, "v1.1.0", "2026-08-22", "https://github.com/pvarki/repo")

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
        "* **cli:** add changelog command "
        "([aaaaaaa](https://github.com/pvarki/repo/commit/aaaaaaaaaa))"
    ) in md


def test_render_without_a_url_falls_back_to_the_short_sha():
    commit = Commit.parse("dddddddddd", "feat!: drop python 3.10", "")
    assert "* drop python 3.10 (ddddddd)" in render([commit], "v1.1.0", "2026-08-22")


def test_empty_range():
    assert "_No notable changes._" in render([], "v1.1.0", "2026-08-22")

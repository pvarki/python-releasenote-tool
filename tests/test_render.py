"""The whole range rendered, from pull request bodies to the files a build writes."""

import pytest
from conftest import REPO

from releasenote_tool import notes
from releasenote_tool.changelog import Commit
from releasenote_tool.cli import documents

# Repetitive shas on purpose, a realistic one reads as a high entropy string to detect-secrets.
LOG = [
    ("aaaaaaaaaaaa", "feat(map): draw migration routes as one line", ""),
    ("bbbbbbbbbbbb", "feat(sightings): filter by species", ""),
    ("cccccccccccc", "fix(export): keep the last sighting", ""),
    ("dddddddddddd", "chore(deps): bump the tile renderer", ""),
    ("eeeeeeeeeeee", "refactor!: rename the tile cache", ""),
]

VERSION, DATE = "v1.2.0", "2026-08-29"

# Fixtures that must contribute nothing: no markers, an untouched placeholder, text with no
# heading above it, and an empty block.
SILENT = ["no-section", "placeholder", "headless", "empty-block"]


def commits():
    return [commit for commit in (Commit.parse(*entry) for entry in LOG) if commit]


def changes(pulls):
    return [change for pull in pulls for change in notes.changes(pull)]


def test_release_notes(pulls, file_regression):
    markdown = notes.render(changes(pulls), VERSION, DATE)
    file_regression.check(markdown, basename="release-notes", extension=".md")


def test_release_body(pulls, file_regression):
    files = documents(commits(), changes(pulls), VERSION, DATE, REPO)
    file_regression.check(files["release-body.md"], basename="release-body", extension=".md")


@pytest.mark.parametrize("name", SILENT)
def test_pull_requests_that_contribute_nothing(pull, name):
    assert notes.changes(pull(name)) == []


def test_every_change_links_the_pull_request_it_came_from(pulls):
    for change in changes(pulls):
        assert f"([#{change.number}](" in change.markdown()


def test_one_pull_request_contributes_one_entry_per_heading(pull):
    assert [change.title for change in notes.changes(pull("wombats"))] == [
        "Scat photos are classified for you",
        "Filter sightings by species",
        "Exports keep the last sighting",
    ]


def test_a_note_written_as_bullets_keeps_its_list(pull):
    first, second = notes.changes(pull("bees"))
    assert first.body.startswith("- brood, stores and temper sit on one line per hive\n")
    assert first.body.count("\n- ") == 2
    assert second.body.count("\n- ") == 2


def test_a_lead_in_sentence_stays_above_its_bullets(pull):
    (change,) = notes.changes(pull("narwhals"))
    assert change.body.startswith("A narwhal tusk is really a tooth")
    assert "\n- length in centimetres, spiral direction optional\n" in change.body


def test_a_screenshot_comes_along(pull):
    (change,) = notes.changes(pull("flamingos"))
    assert "![The sighting card showing the plumage scale](" in change.body


def test_a_subheading_stays_inside_its_entry(pull):
    (change,) = notes.changes(pull("subheadings"))
    assert "#### On the web" in change.body
    assert "#### On mobile" in change.body


def test_an_unterminated_block_stops_at_the_next_section(pull):
    (change,) = notes.changes(pull("unterminated"))
    assert change.title == "Migration routes on the map"
    assert "Anything Else" not in change.body


def test_a_placeholder_left_beside_a_real_entry(pull):
    assert [change.title for change in notes.changes(pull("placeholder-plus-real"))] == [
        "Colony size estimated from one photo"
    ]


def test_guidance_comments_never_reach_the_notes(pulls):
    for change in changes(pulls):
        assert "<!--" not in change.markdown()


def test_a_range_without_user_facing_changes_gets_the_changelog_alone():
    files = documents(commits(), [], VERSION, DATE, REPO)
    assert "release-notes.md" not in files
    assert files["release-body.md"] == files["changelog.md"]

import re
import subprocess

import click
import pytest

from releasenote_tool import notes
from releasenote_tool.notes import BATCH, changes, entries, pull_requests, slug

ONE = """## Description
The pouch logic moved to `marsupial.py`, reviewers should start there.

## User-Facing Changes
<!-- releasenote:start -->
### Wombats leave tidy droppings
Wombat droppings come out cube shaped, so they stay put on a rock instead of rolling off.
<!-- releasenote:end -->

## Anything Else You'd Like to Mention
Nothing.
"""

SEVERAL = """## User-Facing Changes
<!-- releasenote:start -->
### Otters hold hands
Sleeping otters no longer drift apart overnight.

### Pups float on their own
Sea otter pups cannot sink even if they try.
<!-- releasenote:end -->
"""

PLACEHOLDER = """## User-Facing Changes
<!-- releasenote:start -->
### Short title of the change
A few sentences describing the change to a user.
<!-- releasenote:end -->
"""

COMMENTED = """## User-Facing Changes
<!--
Used in the release notes, write from the user's point of view.
One ### per change, a screenshot can be included.
-->
<!-- releasenote:start -->
### Flamingos turn pink
<!-- remember to attach the screenshot -->
Flamingos are born grey and take their pink from the brine shrimp they eat.
<!-- releasenote:end -->
"""

HEADLESS = """## User-Facing Changes
<!-- releasenote:start -->
A group of flamingos is called a flamboyance, and nobody wrote a heading for it.
<!-- releasenote:end -->
"""

NO_SECTION = """## Description
Reverts d4e5f6a, no user-visible effect.

## Anything Else You'd Like to Mention
Octopuses have three hearts, unrelated.
"""


def pull_request(body, number=118, title="fix: keep the otters together"):
    return {
        "body": body,
        "number": number,
        "title": title,
        "url": f"https://example.com/example/test/pull/{number}",
    }


def test_a_change_is_headed_by_its_own_title_and_links_the_pull_request():
    (change,) = changes(pull_request(ONE))
    assert change.markdown() == (
        "### Wombats leave tidy droppings "
        "([#118](https://example.com/example/test/pull/118))\n\n"
        "Wombat droppings come out cube shaped, so they stay put on a rock instead of rolling off."
    )


def test_the_rest_of_the_pull_request_body_is_left_out():
    (change,) = changes(pull_request(ONE))
    assert "marsupial.py" not in change.body
    assert "Anything Else" not in change.body


def test_one_pull_request_can_contribute_several_changes():
    assert [change.title for change in changes(pull_request(SEVERAL))] == [
        "Otters hold hands",
        "Pups float on their own",
    ]
    assert [change.number for change in changes(pull_request(SEVERAL))] == [118, 118]


def test_guidance_comments_are_stripped():
    (change,) = changes(pull_request(COMMENTED))
    assert change.title == "Flamingos turn pink"
    assert change.body == (
        "Flamingos are born grey and take their pink from the brine shrimp they eat."
    )


def test_pull_requests_without_user_facing_changes():
    assert changes(pull_request(PLACEHOLDER)) == []
    assert changes(pull_request(HEADLESS)) == []
    assert changes(pull_request(NO_SECTION)) == []
    assert changes(pull_request(None)) == []


def test_a_placeholder_entry_left_behind_does_not_take_the_real_one_with_it():
    body = """## User-Facing Changes
<!-- releasenote:start -->
### Short title of the change
A few sentences describing the change to a user.

### Octopuses keep their hearts
Two of the three hearts stop while an octopus swims, which is why it prefers to crawl.
<!-- releasenote:end -->
"""
    assert [change.title for change in changes(pull_request(body))] == [
        "Octopuses keep their hearts"
    ]


def test_an_unterminated_block_stops_at_the_next_section():
    body = ONE.replace("<!-- releasenote:end -->\n", "")
    (title, text) = entries(body)[0]
    assert title == "Wombats leave tidy droppings"
    assert "Anything Else" not in text


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.com/example/test", "example/test"),
        ("https://example.com/example/test/", "example/test"),
        ("https://github.com/pvarki/python-releasenote-tool", "pvarki/python-releasenote-tool"),
    ],
)
def test_slug_keeps_the_owner(url, expected):
    assert slug(url) == expected


SLUG = "example/test"
OID_RE = re.compile(r'object\(oid: "([0-9a-f]{40})"\)')


def associated(number, repo=SLUG, merged_at="2026-08-22T15:23:49Z"):
    """One pull request as the association query returns it."""
    return {
        **pull_request(ONE, number),
        "mergedAt": merged_at,
        "repository": {"nameWithOwner": repo},
    }


def sha(index):
    return f"{index:040x}"


@pytest.fixture
def graphql(monkeypatch):
    """Stub gh, answering each batched query from a sha to pull requests mapping."""

    def answer(by_sha):
        asked = []

        def run(*args):
            query = next(arg for arg in args if arg.startswith("query="))
            shas = OID_RE.findall(query)
            asked.append(shas)
            return {
                "data": {
                    "repository": {
                        f"c{index}": (
                            {"associatedPullRequests": {"nodes": by_sha[found]}}
                            if found in by_sha
                            else None
                        )
                        for index, found in enumerate(shas)
                    }
                }
            }

        monkeypatch.setattr(notes, "_gh", run)
        return asked

    return answer


def test_a_pull_request_several_commits_belong_to_is_listed_once(graphql):
    graphql({sha(1): [associated(7)], sha(2): [associated(7)], sha(3): [associated(8)]})

    listed = pull_requests(SLUG, [sha(1), sha(2), sha(3)])

    assert [pull["number"] for pull in listed] == [7, 8]
    assert set(listed[0]) == {"number", "title", "body", "url"}


def test_a_pull_request_still_open_is_not_a_release_note(graphql):
    graphql({sha(1): [associated(7, merged_at=None)]})

    assert pull_requests(SLUG, [sha(1)]) == []


def test_a_pull_request_from_another_repository_stays_there(graphql):
    graphql({sha(1): [associated(7, repo="example/fork")]})

    assert pull_requests(SLUG, [sha(1)]) == []


def test_a_sha_github_does_not_know_is_skipped(graphql):
    graphql({sha(2): [associated(7)]})

    assert [pull["number"] for pull in pull_requests(SLUG, [sha(1), sha(2)])] == [7]


def test_a_long_range_is_asked_in_batches(graphql):
    asked = graphql({})

    assert pull_requests(SLUG, [sha(index) for index in range(BATCH + 1)]) == []
    assert [len(batch) for batch in asked] == [BATCH, 1]


def test_a_range_with_no_commits_asks_github_nothing(graphql):
    asked = graphql({})

    assert pull_requests(SLUG, []) == []
    assert asked == []


def test_a_missing_gh_points_at_the_container_image(monkeypatch):
    def absent(*_args, **_kwargs):
        raise FileNotFoundError(2, "No such file or directory", "gh")

    monkeypatch.setattr(notes.subprocess, "run", absent)
    with pytest.raises(click.ClickException, match="container image"):
        notes.pull_request("example/test", 1)


def test_gh_failing_carries_its_own_error(monkeypatch):
    def failed(*args, **_kwargs):
        return subprocess.CompletedProcess(args, 1, "", "gh: Not Found (HTTP 404)\n")

    monkeypatch.setattr(notes.subprocess, "run", failed)
    with pytest.raises(click.ClickException, match="HTTP 404"):
        notes.pull_request("example/test", 1)

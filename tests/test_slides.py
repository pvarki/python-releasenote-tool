"""The Marp deck, rendered from the same pull request fixtures as the release notes."""

from conftest import REPO

from releasenote_tool import notes, slides

VERSION, DATE = "v1.2.0", "2026-08-29"


def entries(pulls):
    return [change for pull in pulls for change in notes.changes(pull)]


def change(body, title="Otter pairs stay linked overnight", number=118):
    return notes.Change(title, body, number, f"{REPO}/pull/{number}")


def deck(markdown):
    """The slides of a rendered deck, front matter dropped."""
    return markdown.removeprefix(f"{slides.FRONT_MATTER}\n\n").split(slides.SEPARATOR)


def test_slides(pulls, file_regression):
    markdown = slides.render(entries(pulls), VERSION, DATE, REPO)
    file_regression.check(markdown, basename="slides", extension=".md")


def test_the_deck_opens_with_marp_front_matter(pulls):
    assert slides.render(entries(pulls), VERSION, DATE, REPO).startswith(slides.FRONT_MATTER)


def test_the_title_slide_names_the_repository_and_the_version(pulls):
    first = deck(slides.render(entries(pulls), VERSION, DATE, REPO))[0]
    assert "# example/test" in first
    assert f"## {VERSION} — {DATE}" in first


def test_the_title_slide_falls_back_to_the_version_without_a_repository():
    first = deck(slides.render([], VERSION, DATE, None))[0]
    assert f"# {VERSION}" in first
    assert f"## {DATE}" in first


def test_one_slide_per_change_after_the_title(pulls):
    changes = entries(pulls)
    assert len(deck(slides.render(changes, VERSION, DATE, REPO))) == len(changes) + 1


def test_every_slide_footers_the_pull_request_it_came_from(pulls):
    for slide in deck(slides.render(entries(pulls), VERSION, DATE, REPO))[1:]:
        assert "_footer:" in slide


def test_guidance_comments_never_reach_the_deck(pulls):
    assert "releasenote:" not in slides.render(entries(pulls), VERSION, DATE, REPO)


def test_a_rule_inside_a_change_does_not_split_its_slide():
    markdown = slides.render([change("Before\n\n---\n\nAfter")], VERSION, DATE, REPO)
    assert len(deck(markdown)) == 2
    assert "<hr />" in markdown


def test_a_heading_underline_is_left_alone():
    markdown = slides.render([change("Overnight\n---\nOtters hold hands.")], VERSION, DATE, REPO)
    assert "Overnight\n---\nOtters hold hands." in markdown


def test_a_long_change_is_marked_dense():
    body = "\n".join(f"- sighting {number}" for number in range(slides.DENSE_LINES + 1))
    assert "_class: dense" in slides.render([change(body)], VERSION, DATE, REPO)


def test_a_short_change_is_not():
    body = "Sea otters hold hands while they sleep so they do not drift apart."
    assert "_class: dense" not in slides.render([change(body)], VERSION, DATE, REPO)

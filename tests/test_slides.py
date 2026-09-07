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
    assert f"## {VERSION} ({DATE})" in first


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


def test_soft_wrapped_prose_becomes_one_line():
    body = "Sea otters hold hands while they sleep\nso they do not drift apart."
    markdown = slides.render([change(body)], VERSION, DATE, REPO)
    assert "sleep so they" in markdown


def test_a_wrapped_bullet_keeps_its_marker_and_gains_the_rest():
    assert slides.unwrap("- length in centimetres,\n  spiral direction optional") == (
        "- length in centimetres, spiral direction optional"
    )


def test_what_owns_its_own_line_keeps_it():
    body = "#### On the web\nThe sidebar stays open.\n\n![A card](https://example.com/card.png)"
    assert slides.unwrap(body) == body


def test_a_line_break_someone_asked_for_survives():
    assert slides.unwrap("Otters hold hands  \nPups float alone") == (
        "Otters hold hands  \nPups float alone"
    )


def test_fenced_code_is_left_as_written():
    body = "Run it with:\n\n```sh\nreleasenote changes --to v1.2.0\n--out dist\n```"
    assert slides.unwrap(body) == body


def test_a_long_change_is_marked_dense():
    body = "\n".join(f"- sighting {number}" for number in range(slides.DENSE_LINES + 1))
    assert "_class: dense" in slides.render([change(body)], VERSION, DATE, REPO)


def test_a_short_change_is_not():
    body = "Sea otters hold hands while they sleep so they do not drift apart."
    assert "_class: dense" not in slides.render([change(body)], VERSION, DATE, REPO)


IMAGE = '<img alt="image" src="https://example.com/otters.png" />'


def test_an_image_under_a_bullet_is_broken_out_of_the_list():
    """Markdown folds a lazy continuation into the <li>, which nothing can then size."""
    assert slides.unwrap(f"- holding hands\n{IMAGE}") == f"- holding hands\n\n{IMAGE}"


def test_an_image_counts_as_the_space_the_theme_gives_it():
    bullets = "\n".join(f"- sighting {number}" for number in range(6))

    assert "_class: dense" in slides.render([change(f"{bullets}\n{IMAGE}")], VERSION, DATE, REPO)
    assert "_class: dense" not in slides.render([change(bullets)], VERSION, DATE, REPO)

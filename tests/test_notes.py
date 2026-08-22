from releasenote_tool.notes import block, slug, user_facing, window

BULLETS = """## User-Facing Summary
- Otters keep holding hands while they sleep so they don't drift apart
- Sea otter pups float on their own, they cannot sink even if they try

## Why It's Good for the Product (Release Goal)
- Fewer otters lost at sea
"""

PROSE = """Reviewers: the pouch logic moved to `marsupial.py`, see the diff there first.

## User-Facing Summary

Wombat droppings come out cube shaped, so they stay put on a rock instead of rolling off.
"""

EMPTY = """## User-Facing Summary

## Why It's Good for the Product (Release Goal)
- Internal cleanup, nothing visible
"""

NO_SECTION = "Reverts d4e5f6a. A group of flamingos is called a flamboyance, unrelated."


def pull_request(body, number=118, title="fix: keep the otters together"):
    return {
        "body": body,
        "number": number,
        "title": title,
        "url": f"https://github.com/example/widget/pull/{number}",
    }


def test_bullets_are_wrapped_in_a_heading_linking_the_pull_request():
    assert block(pull_request(BULLETS)) == (
        "### fix: keep the otters together "
        "([#118](https://github.com/example/widget/pull/118))\n\n"
        "- Otters keep holding hands while they sleep so they don't drift apart\n"
        "- Sea otter pups float on their own, they cannot sink even if they try"
    )


def test_the_release_goal_section_is_left_out():
    assert "Release Goal" not in block(pull_request(BULLETS))
    assert "lost at sea" not in block(pull_request(BULLETS))


def test_description_above_the_heading_is_left_out():
    assert user_facing(PROSE) == (
        "Wombat droppings come out cube shaped, so they stay put on a rock instead of rolling off."
    )


def test_pull_requests_without_user_facing_content():
    assert block(pull_request(EMPTY)) is None
    assert block(pull_request(NO_SECTION)) is None
    assert block(pull_request(None)) is None


def test_slug():
    assert slug("https://github.com/example/widget") == "example/widget"


def test_the_window_starts_after_the_previous_tag():
    assert window("2026-08-22T14:10:43+03:00", "2026-08-22T15:23:49+03:00") == (
        "2026-08-22T14:10:44+03:00..2026-08-22T15:23:49+03:00"
    )
    assert window(None, "2026-08-22T15:23:49+03:00") == "<=2026-08-22T15:23:49+03:00"

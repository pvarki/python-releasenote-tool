"""The names a build gives the files it writes."""

from conftest import REPO

from releasenote_tool import assets

STEM = "example-integration-1.1.0"


def test_the_product_comes_from_the_origin_repository():
    assert assets.project(".", REPO, None) == "test"


def test_a_given_product_wins_over_the_origin_repository():
    assert assets.project(".", REPO, "example-integration") == "example-integration"


def test_a_repository_without_an_origin_falls_back_to_its_directory(tmp_path):
    checkout = tmp_path / "hive-tracker"
    checkout.mkdir()
    assert assets.project(str(checkout), None, None) == "hive-tracker"


def test_a_release_tag_loses_its_leading_v():
    assert assets.version("v1.1.0") == "1.1.0"


def test_a_ref_that_merely_starts_with_v_keeps_it():
    assert assets.version("verify-fix") == "verify-fix"


def test_a_ref_with_a_slash_stays_one_path_component():
    assert assets.version("release/1.2") == "release-1.2"


def test_a_ref_cannot_climb_out_of_the_output_directory():
    assert assets.version("../../etc/passwd") == "etc-passwd"


def test_the_release_body_keeps_a_fixed_name():
    assert assets.names(STEM)["release-body"] == assets.BODY


def test_the_deck_does_not_take_the_prose_notes_name():
    filenames = assets.names(STEM)
    assert filenames["slides"] != filenames["release-notes"]


def test_a_render_takes_the_prose_notes_name():
    assert assets.rendered(STEM, "pdf") == f"{STEM}-release-notes.pdf"

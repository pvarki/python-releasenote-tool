"""The marp invocations, checked without marp installed."""

import pathlib
import subprocess

import click
import pytest
from click.testing import CliRunner

from releasenote_tool import export
from releasenote_tool.cli import main

DECK = pathlib.Path("dist/slides.md")


def argv(fmt):
    with export.theme() as css:
        return export.command(DECK, export.target(DECK, fmt), css)


def test_a_render_sits_beside_its_deck():
    assert export.target(DECK, "pptx") == pathlib.Path("dist/slides.pptx")


def test_an_out_directory_takes_the_render_instead():
    assert export.target(DECK, "pdf", pathlib.Path("assets")) == pathlib.Path("assets/slides.pdf")


def test_the_invocation_names_the_deck_the_theme_and_the_output():
    line = argv("pdf")
    assert line[:2] == ["marp", "dist/slides.md"]
    assert line[line.index("--theme") + 1].endswith(export.THEME)
    assert line[line.index("-o") + 1] == "dist/slides.pdf"


def test_the_format_comes_from_the_output_extension():
    assert not {"--pdf", "--pptx"} & set(argv("pdf") + argv("pptx"))


def test_only_the_pptx_run_asks_for_editable_text():
    assert "--pptx-editable" in argv("pptx")
    assert "--pptx-editable" not in argv("pdf")


def test_the_bundled_theme_is_a_marp_theme():
    with export.theme() as css:
        assert css.read_text().startswith("/* @theme releasenote */")


def test_a_missing_marp_points_at_the_container_image(monkeypatch):
    def absent(*_args, **_kwargs):
        raise FileNotFoundError(2, "No such file or directory", "marp")

    monkeypatch.setattr(export.subprocess, "run", absent)
    with pytest.raises(click.ClickException, match="container image"):
        export.run(DECK, export.target(DECK, "pdf"))


def test_marp_failing_carries_its_own_error(monkeypatch):
    def failed(*args, **_kwargs):
        return subprocess.CompletedProcess(args, 1, "", "Error: no such theme\n")

    monkeypatch.setattr(export.subprocess, "run", failed)
    with pytest.raises(click.ClickException, match="no such theme"):
        export.run(DECK, export.target(DECK, "pdf"))


def test_slides_without_an_out_directory_is_refused():
    result = CliRunner().invoke(main, ["changes", "--to", "v1.0.0", "--slides", "pdf"])
    assert result.exit_code != 0
    assert "--out" in result.output

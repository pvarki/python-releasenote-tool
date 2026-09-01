"""Slide exports rendered by marp-cli, one invocation per format."""

import pathlib
import subprocess  # nosec B404
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import as_file, files

import click

FORMATS = ("pdf", "pptx")
THEME = "default.css"
MISSING = (
    "marp is not on PATH. Install @marp-team/marp-cli, or run this from the tool's container image."
)


@contextmanager
def theme() -> Iterator[pathlib.Path]:
    """The bundled Marp theme as a real path, unpacked first if the package is zipped."""
    with as_file(files("releasenote_tool") / "templates" / THEME) as path:
        yield path


def target(source: pathlib.Path, fmt: str, out: pathlib.Path | None = None) -> pathlib.Path:
    """Where a format lands: beside the deck, or in `out` when one is given."""
    rendered = source.with_suffix(f".{fmt}")
    return out / rendered.name if out else rendered


def command(source: pathlib.Path, rendered: pathlib.Path, css: pathlib.Path) -> list[str]:
    """The marp invocation for one output. Its format comes from the target's extension."""
    argv = ["marp", str(source), "--theme", str(css), "-o", str(rendered)]
    if rendered.suffix == ".pptx":
        # Real text boxes instead of one image per slide. Experimental upstream.
        argv.append("--pptx-editable")
    return argv


def run(source: pathlib.Path, rendered: pathlib.Path) -> None:
    with theme() as css:
        try:
            result = subprocess.run(  # nosec
                command(source, rendered, css), capture_output=True, text=True, check=False
            )
        except FileNotFoundError as absent:
            raise click.ClickException(MISSING) from absent
    if result.returncode:
        raise click.ClickException(f"marp failed on {rendered.name}: {result.stderr.strip()}")

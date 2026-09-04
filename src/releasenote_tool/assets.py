"""Names for the files a build writes, so an asset still says what it is once downloaded."""

import pathlib
import re

from .notes import slug

BODY = "release-body.md"

UNSAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")
LEADING_V_RE = re.compile(r"^v(?=\d)")


def safe(text: str) -> str:
    """A filename fragment, with anything that could separate or open a path taken out."""
    return UNSAFE_RE.sub("-", text).strip("-.")


def project(repo: str, url: str | None, product: str | None) -> str:
    """What the release is called: the given product, the origin repository, or its directory."""
    if product:
        return safe(product)
    if url:
        return safe(slug(url).split("/")[-1])
    return safe(pathlib.Path(repo).resolve().name)


def version(label: str) -> str:
    """A version as a filename: a release tag's leading v dropped, the rest made safe."""
    return safe(LEADING_V_RE.sub("", label))


def names(stem: str) -> dict[str, str]:
    """Filename per document kind. The release body keeps a fixed name for automation to read."""
    return {
        "changelog": f"{stem}-changelog.md",
        "release-notes": f"{stem}-release-notes.md",
        "release-body": BODY,
        "slides": f"{stem}-slides.md",
    }


def rendered(stem: str, fmt: str) -> str:
    """A deck's renders take the prose notes' name, not the deck's own."""
    return f"{names(stem)['release-notes'].removesuffix('.md')}.{fmt}"

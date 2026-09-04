#!/bin/sh
set -eu

IMAGE_TAG="local/releasenote-tool-test"
OUT="$(mktemp -d)"

docker build --target production -t "${IMAGE_TAG}" .

docker run --rm \
  --user "$(id -u):$(id -g)" \
  --volume "${PWD}:/workspace" \
  --volume "${OUT}:/out" \
  "${IMAGE_TAG}" \
  slides tests/data/expected/slides.md --format pdf --format pptx --out /out

test "$(head -c 5 "${OUT}/slides.pdf")" = '%PDF-'

python3 - "${OUT}/slides.pptx" <<'PY'
import re
import sys
import zipfile

deck = zipfile.ZipFile(sys.argv[1])
slides = sorted(
    (name for name in deck.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
    key=lambda name: int(re.search(r"\d+", name).group()),
)
assert len(slides) > 1, f"pptx has {len(slides)} slides"

# No text runs means LibreOffice was missing and every slide is a flat image.
text = re.findall(r"<a:t>(.*?)</a:t>", deck.read(slides[1]).decode())
assert text, "pptx carries no editable text"

print(f"{len(slides)} slides, {len(text)} text runs on the first change slide")
PY

# releasenote-tool

Generates a technical changelog from the conventional commits in a git tag range, and user-facing
release notes from the pull requests in that range, for use in CI.

## Usage

```sh
releasenote changelog --to v1.1.0                  # to stdout, --from defaults to the previous tag
releasenote changelog --from v1.0.0 --to v1.1.0
releasenote changelog --to v1.1.0 --out dist       # writes dist/changelog.md
releasenote changelog --repo ../other-repo --to v1.1.0
```

Each entry links to its commit on the origin remote; override the base with `--url`.

`build` adds the user-facing release notes on top of that changelog:

```sh
releasenote build --from v1.0.0 --to v1.1.0  # release body to stdout
releasenote build --to v1.1.0 --out dist     # changelog.md, release-notes.md, release-body.md, slides.md
```

The notes come from the `<!-- releasenote:start -->` block of every pull request merged in the
range, one entry per `###` heading inside it; the rest of the body is left out. A range where no
pull request filled that block gets the changelog alone. Needs `gh` on PATH and authenticated
(`GH_TOKEN: ${{ github.token }}` in Actions).

`feat` goes under Features, `fix` under Fixes, and `build`, `chore`, `ci`, `docs`, `perf`,
`refactor`, `revert`, `style` and `test` under Other changes; a `!` or a `BREAKING CHANGE:` footer
puts an entry under Breaking changes instead. Merge commits, a commit whose type is outside that
set — a typo, usually — and anything not shaped like a conventional commit are left out entirely,
subject line and body both.

## Slides

`slides.md` is a [Marp](https://marp.app) deck of the same notes: a title slide, then one slide
per user-facing change, each footing the pull request it came from. `--slides` renders it, one
flag per format, and needs `--out`:

```sh
releasenote build --to v1.1.0 --out dist --slides pdf --slides pptx
releasenote slides dist/slides.md --format pdf   # render an existing deck, no git or GitHub needed
```

Rendering needs `marp` on PATH, a Chromium for the pdf and LibreOffice for the pptx, which is what
the container image carries:

```sh
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --volume "$PWD:/workspace" \
  --env GH_TOKEN \
  ghcr.io/pvarki/releasenote-tool:0.1.0 \
  build --to v1.1.0 --out dist --slides pdf --slides pptx
```

## Development

```sh
uv sync --extra dev
uv run pytest
uv run pytest --force-regen   # after an intentional change to the rendered output
uv run prek run --all-files
sh tests/test_image.sh        # builds the image and renders in it, needs docker
```

`tests/data/pulls` holds pull request bodies covering what the template produces, and
`tests/data/expected` the markdown they render to. Those are checked with
[pytest-regressions](https://pytest-regressions.readthedocs.io); `--force-regen` rewrites them,
so read the diff before committing it.

The slide styling lives in `src/releasenote_tool/templates/default.css`, a Marp theme. To see a
change, render a deck and look at it (needs marp locally, otherwise run it through the image):

```sh
releasenote slides tests/data/expected/slides.md --format pdf --out dist
```

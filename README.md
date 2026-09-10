# releasenote-tool

Generates a technical changelog from the conventional commits in a git tag range, and user-facing
release notes from the pull requests in that range, for use in CI.

You need a local clone of the repository, and `--repo` is the path to it, default `.`. Nothing is
cloned or fetched for you, so the range has to be there already: full history and tags, which in
Actions means `fetch-depth: 0`.

## Usage

```sh
releasenote commits --to v1.1.0                    # to stdout, --from defaults to the previous tag
releasenote commits --from v1.0.0 --to v1.1.0
releasenote commits --to v1.1.0 --out dist         # writes dist/<product>-1.1.0-changelog.md
releasenote commits --repo ../other-repo --to v1.1.0
```

Each entry links to its commit on the origin remote of that clone.

`changes` adds the user-facing release notes on top of that changelog:

```sh
releasenote changes --from v1.0.0 --to v1.1.0  # release body to stdout
releasenote changes --to v1.1.0 --out dist     # see Output files
releasenote changes --to HEAD --pr 12          # the range plus pull request 12, open or not
```

`commits` is pure git. `changes` uses git and `gh`.

The notes come from the `<!-- releasenote:start -->` block of every pull request merged in the
range, one entry per `###` heading inside it; the rest of the body is ignored. If no pull request
filled that block, you get the changelog alone. Needs `gh` on PATH and authenticated
(`GH_TOKEN: ${{ github.token }}` in Actions).

A pull request only reaches the range once it has merged, `--pr` reads one by number whatever
its state and puts it at the top, which is how CI previews an open one against the release it is
headed for. Passing a number the range already covers changes nothing.

`feat` goes under Features, `fix` under Fixes, and `build`, `chore`, `ci`, `docs`, `perf`,
`refactor`, `revert`, `style` and `test` under Other changes. A `!` or a `BREAKING CHANGE:` footer
puts an entry under Breaking changes instead.

Left out entirely: merge commits, anything not shaped like a conventional commit, a type outside
that set, and commits that bump the project's own version, which CI makes every pull request carry.

## Output files

Every file leads with the product and the version, so an asset still says what it is once it has
been downloaded or attached to a release:

```sh
releasenote changes --to v1.1.0 --out dist --product example-integration
```

```
dist/
  example-integration-1.1.0-changelog.md      the technical changelog
  example-integration-1.1.0-release-notes.md  the user-facing notes
  example-integration-1.1.0-slides.md         the deck the renders come from
  release-body.md                             the notes and the changelog in one
```

`--product` defaults to the name of the origin repository, which is not always what the product is
called. `--release` gives the version the documents claim when the ref does not carry one, which is
what a preview built from `--to HEAD` wants. Both work on `commits` too. A `/` in a ref is
flattened, so `--to release/1.2` stays one filename.

`release-body.md` keeps a fixed name on purpose: it is the file automation reads, so
`gh release create --notes-file dist/release-body.md` needs no version in the path. It is also the
only one a second run into the same directory overwrites rather than sits beside.

## Slides

The `-slides.md` file is a [Marp](https://marp.app) deck of the same notes: a title slide, then one
slide per user-facing change, footed with the pull request it came from. `--slides` renders it, one
flag per format, and needs `--out`:

```sh
releasenote changes --to v1.1.0 --out dist --slides pdf --slides pptx
releasenote slides dist/example-integration-1.1.0-slides.md --format pdf
```

A render from `changes` takes the release notes' name, `example-integration-1.1.0-release-notes.pdf`,
because that is the document someone is handed. `releasenote slides` names its renders after the
deck you give it instead, since it never sees a product or a version and needs no git or GitHub.

Rendering needs `marp` on PATH, Chromium for the pdf and LibreOffice for the pptx. The container
image ships all three:

```sh
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --volume "$PWD:/workspace" \
  --env GH_TOKEN \
  ghcr.io/pvarki/releasenote-tool:1.0.0 \
  changes --to v1.1.0 --out dist --slides pdf --slides pptx
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

Slide styling is `src/releasenote_tool/templates/default.css`, a Marp theme. To see a change,
render a deck and look at it (needs marp locally, or run it through the image):

```sh
releasenote slides tests/data/expected/slides.md --format pdf --out dist
```

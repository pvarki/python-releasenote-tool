# releasenote-tool

Generates a technical changelog from conventional commits in a git tag range, for use in CI.

Later phases add user-facing release notes assembled from pull request bodies (Markdown + Marp
slides) and a platform-level aggregate across component repositories.

## Usage

```sh
releasenote changelog --to v1.1.0                  # to stdout, --from defaults to the previous tag
releasenote changelog --from v1.0.0 --to v1.1.0
releasenote changelog --to v1.1.0 --out dist       # writes dist/changelog.md
releasenote changelog --repo ../other-repo --to v1.1.0
```

Each entry links to its commit on the origin remote; override the base with `--url`.

`feat` goes under Features, `fix` under Fixes, anything else under Other changes, and a `!` or a
`BREAKING CHANGE:` footer under Breaking changes. Merge commits and commits that are not
conventional commits are left out.

## Development

```sh
uv sync --extra dev
uv run pytest
```

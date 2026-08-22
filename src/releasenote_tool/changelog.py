"""Technical changelog from conventional commits in a git tag range."""

import re
import subprocess  # nosec B404
from dataclasses import dataclass

SUBJECT_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?: (?P<description>.+)$",
    re.IGNORECASE,
)
BREAKING_FOOTER_RE = re.compile(r"^BREAKING[ -]CHANGE:", re.MULTILINE)

SECTIONS = {
    "breaking": "Breaking changes",
    "feat": "Features",
    "fix": "Fixes",
    "other": "Other changes",
}

RECORD, FIELD = "\x1e", "\x1f"


@dataclass(frozen=True)
class Commit:
    """A conventional commit, already sorted into the section it renders under."""

    section: str
    scope: str | None
    description: str
    sha: str

    @classmethod
    def parse(cls, sha: str, subject: str, body: str) -> "Commit | None":
        """None for anything that is not a conventional commit."""
        match = SUBJECT_RE.match(subject)
        if not match:
            return None
        type_ = match["type"].lower()
        if match["breaking"] or BREAKING_FOOTER_RE.search(body):
            section = "breaking"
        else:
            section = type_ if type_ in ("feat", "fix") else "other"
        return cls(section, match["scope"], match["description"], sha[:7])

    def __str__(self) -> str:
        scope = f"**{self.scope}:** " if self.scope else ""
        return f"* {scope}{self.description} ({self.sha})"


def _git(repo: str, *args: str) -> str:
    return subprocess.run(  # nosec
        ["git", "-C", repo, *args], capture_output=True, text=True, check=True
    ).stdout


def commits_in_range(repo: str, start: str | None, end: str) -> list[Commit]:
    log = _git(
        repo,
        "log",
        "--no-merges",
        f"--format={FIELD.join(('%H', '%s', '%b'))}{RECORD}",
        f"{start}..{end}" if start else end,
    )
    records = (record.strip("\n").split(FIELD) for record in log.split(RECORD) if record.strip())
    parsed = (Commit.parse(*record) for record in records)
    return [commit for commit in parsed if commit]


def render(commits: list[Commit], version: str, date: str) -> str:
    blocks = [f"## {version} ({date})"]
    for section, heading in SECTIONS.items():
        lines = [str(commit) for commit in commits if commit.section == section]
        if lines:
            blocks += [f"### {heading}", "\n".join(lines)]
    if len(blocks) == 1:
        blocks.append("_No notable changes._")
    return "\n\n".join(blocks) + "\n"


def previous_tag(repo: str, to: str) -> str | None:
    try:
        return _git(repo, "describe", "--tags", "--abbrev=0", f"{to}^").strip()
    except subprocess.CalledProcessError:
        return None


def date_of(repo: str, to: str) -> str:
    return _git(repo, "log", "-1", "--format=%cs", to).strip()

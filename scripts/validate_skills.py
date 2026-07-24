"""Validate public skill metadata and documentation links."""

from pathlib import Path
import re


ROOT = Path(__file__).parent.parent
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
FIELD = re.compile(r"^(name|description):\s*(.+)$", re.MULTILINE)
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FORBIDDEN_PATHS = (
    "/Users/",
    "~/Code/",
    "~/Documents/",
    "~/backups/",
    "~/.local/",
    "~/.aws/",
    "~/.ssh/",
)


def metadata(path: Path) -> dict[str, str]:
    """Return the required frontmatter fields from a skill file."""
    match = FRONTMATTER.match(path.read_text())
    if match is None:
        raise ValueError(f"{path}: missing frontmatter")

    return dict(FIELD.findall(match.group(1)))


def validate_skill(path: Path) -> None:
    """Validate one skill's identity and public-path constraints."""
    fields = metadata(path)
    if fields.get("name") != path.parent.name:
        raise ValueError(f"{path}: name must match its directory")
    if not fields.get("description"):
        raise ValueError(f"{path}: missing description")

    contents = path.read_text()
    for forbidden_path in FORBIDDEN_PATHS:
        if forbidden_path in contents:
            raise ValueError(f"{path}: contains machine-specific path {forbidden_path}")


def validate_links(path: Path) -> None:
    """Validate local Markdown links in a documentation file."""
    for target in LINK.findall(path.read_text()):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (ROOT / target).exists():
            raise ValueError(f"{path}: broken link {target}")


def main() -> None:
    """Run every repository validation."""
    skill_files = sorted(ROOT.glob("*/SKILL.md"))
    if not skill_files:
        raise ValueError("no skills found")

    for skill_file in skill_files:
        validate_skill(skill_file)
    for documentation_file in (ROOT / "README.md", ROOT / "SKILLS_STANDARD.md"):
        validate_links(documentation_file)

    print(f"validated {len(skill_files)} skills")


if __name__ == "__main__":
    main()

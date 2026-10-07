#!/usr/bin/env python3
"""Validate this skill package without third-party dependencies."""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9-]+$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ALLOWED_FRONTMATTER_KEYS = {"name", "description"}
FALLBACK_STDLIB = {
    "__future__", "argparse", "ast", "collections", "html", "json", "math",
    "pathlib", "re", "subprocess", "sys", "tempfile", "typing",
}


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    normalized = content.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = normalized.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md has no closing frontmatter delimiter")

    values: dict[str, str] = {}
    for number, line in enumerate(normalized[4:end].splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0].isspace() or ":" not in line:
            raise ValueError(
                f"frontmatter line {number} must be a top-level key with a one-line scalar value"
            )
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key in values:
            raise ValueError(f"duplicate frontmatter key: {key}")
        if value.startswith(("'", '"')):
            quote = value[0]
            if len(value) < 2 or not value.endswith(quote):
                raise ValueError(f"unterminated quoted value for {key}")
            value = value[1:-1]
            if quote == "'":
                value = value.replace("''", "'")
        values[key] = value
    return values, normalized[end + 5:]


def validate_frontmatter(skill_dir: Path, errors: list[str]) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append("SKILL.md is missing")
        return ""
    try:
        content = skill_md.read_text(encoding="utf-8-sig")
        frontmatter, body = parse_frontmatter(content)
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(str(exc))
        return ""

    unexpected = sorted(set(frontmatter) - ALLOWED_FRONTMATTER_KEYS)
    missing = sorted(ALLOWED_FRONTMATTER_KEYS - set(frontmatter))
    if unexpected:
        errors.append(f"unexpected frontmatter keys: {', '.join(unexpected)}")
    if missing:
        errors.append(f"missing frontmatter keys: {', '.join(missing)}")

    name = frontmatter.get("name", "").strip()
    if not name:
        errors.append("frontmatter name is empty")
    elif not NAME_RE.fullmatch(name) or name.startswith("-") or name.endswith("-") or "--" in name:
        errors.append(f"invalid skill name: {name!r}")
    elif len(name) > 64:
        errors.append("skill name exceeds 64 characters")
    elif name != skill_dir.name:
        errors.append(f"skill name {name!r} does not match directory {skill_dir.name!r}")

    description = frontmatter.get("description", "").strip()
    if not description:
        errors.append("frontmatter description is empty")
    elif len(description) > 1024:
        errors.append("frontmatter description exceeds 1024 characters")
    elif "<" in description or ">" in description:
        errors.append("frontmatter description contains angle brackets")
    elif description.startswith("[TODO:"):
        errors.append("frontmatter description contains a TODO placeholder")

    fence_marker = ""
    fence_length = 0
    for line in body.splitlines():
        fence = re.match(r"^[ \t]*(?:[-+*]|\d+[.)])?[ \t]*(`{3,}|~{3,})(.*)$", line)
        if fence:
            marker = fence.group(1)
            if not fence_marker:
                fence_marker, fence_length = marker[0], len(marker)
            elif marker[0] == fence_marker and len(marker) >= fence_length and not fence.group(2).strip():
                fence_marker, fence_length = "", 0
            continue
        if not fence_marker and re.fullmatch(r"[ ]{0,3}\[TODO:[^\n]*\][ \t]*", line):
            errors.append("SKILL.md contains an unfinished TODO placeholder")
            break
    return content


def validate_references(skill_dir: Path, errors: list[str]) -> None:
    root = skill_dir.resolve()
    for markdown in sorted(skill_dir.rglob("*.md")):
        try:
            content = markdown.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read {markdown.relative_to(skill_dir)}: {exc}")
            continue
        for match in LINK_RE.finditer(content):
            raw = match.group(1).strip()
            if not raw or raw.startswith("#") or "://" in raw or raw.startswith("mailto:"):
                continue
            path_text = raw.split("#", 1)[0].strip()
            if not path_text:
                continue
            target = (markdown.parent / path_text).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                errors.append(f"reference escapes the skill directory: {raw}")
                continue
            if not target.exists():
                errors.append(f"broken reference in {markdown.relative_to(skill_dir)}: {raw}")


def imported_modules(path: Path) -> tuple[set[str], list[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 9))
    modules: set[str] = set()
    relative: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                relative.append(node.module or "<relative>")
            elif node.module:
                modules.add(node.module.split(".", 1)[0])
    return modules, relative


def validate_python_scripts(skill_dir: Path, errors: list[str]) -> None:
    stdlib = set(getattr(sys, "stdlib_module_names", ())) or FALLBACK_STDLIB
    scripts = sorted((skill_dir / "scripts").glob("*.py"))
    if not scripts:
        errors.append("scripts directory contains no Python files")
        return
    for script in scripts:
        try:
            modules, relative = imported_modules(script)
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f"cannot parse {script.relative_to(skill_dir)}: {exc}")
            continue
        third_party = sorted(modules - stdlib - {"__future__"})
        if relative:
            errors.append(f"relative imports in {script.name}: {', '.join(relative)}")
        if third_party:
            errors.append(f"third-party imports in {script.name}: {', '.join(third_party)}")


def run_compiler_self_tests(skill_dir: Path, errors: list[str]) -> None:
    for name in ("compile_board.py", "compile_assignments.py"):
        compiler = skill_dir / "scripts" / name
        if not compiler.is_file():
            errors.append(f"scripts/{name} is missing")
            continue
        completed = subprocess.run(
            [sys.executable, "-I", "-S", str(compiler), "--self-test"],
            cwd=str(skill_dir), capture_output=True, text=True, check=False,
        )
        if completed.returncode:
            detail = (completed.stderr or completed.stdout).strip()
            errors.append(f"{name} self-test failed: {detail or 'no diagnostic output'}")


def main() -> int:
    default_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", nargs="?", type=Path, default=default_dir)
    parser.add_argument("--skip-compiler-self-test", action="store_true")
    args = parser.parse_args()

    skill_dir = args.skill_dir.resolve()
    errors: list[str] = []
    validate_frontmatter(skill_dir, errors)
    validate_references(skill_dir, errors)
    validate_python_scripts(skill_dir, errors)
    if not args.skip_compiler_self_test:
        run_compiler_self_tests(skill_dir, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Skill package validation passed (standard library only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations
import sys
import shutil
from importlib.resources import files
from pathlib import Path

SKILL_NAME = "spectagger"


# Directories to refuse writing a skill into, regardless of --force.
def _protected_dirs() -> set[Path]:
    home = Path.home().resolve()
    return {
        home,
        Path("/").resolve(),
        Path.cwd().resolve(),
        *(p.resolve() for p in home.parents),  # /Users, /home, /
    }


def _validate_dest(dest: str) -> Path:
    root = Path(dest).expanduser().resolve()

    # 1. Refuse obviously wrong roots outright.
    if root in _protected_dirs():
        raise SystemExit(
            f"Refusing to install into {root} — pass a skills directory such as "
            f"~/.claude/skills, not your home or project root."
        )

    # 2. Refuse a dest that is itself the skill dir (would nest or clobber).
    if root.name == SKILL_NAME:
        raise SystemExit(
            f"--dest should be the skills *directory* (e.g. ~/.claude/skills), "
            f"not the skill folder itself. Drop the trailing '{SKILL_NAME}'."
        )

    # 3. Nudge if it doesn't look like a skills dir.
    if root.name != "skills":
        print(
            f"Note: {root} doesn't end in 'skills' — check your agent's docs "
            f"for its skills directory."
        )

    return root


def _bundled_skill_dir() -> Path:
    """Resolve the skill inside the installed package (works from a wheel)."""
    return Path(str(files("spec_tagger") / "agent_skill"))


def install_skill(destination: str, force: bool, dry_run: bool) -> Path:

    src = _bundled_skill_dir()
    root = _validate_dest(destination)
    target = root / SKILL_NAME

    if dry_run:
        print(f"would install: {src} -> {target}")
        return target

    if target.exists():
        if not force:
            raise SystemExit(f"{target} already exists. Pass --force to overwrite.")

        if not (target / "SKILL.md").exists():
            raise SystemExit(
                f"Refusing to delete {target}: it exists but contains no SKILL.md, "
                f"so it may not be a skill directory. Remove it manually if intended."
            )

        if sys.stdin.isatty():
            n = sum(1 for _ in target.rglob("*"))
            reply = input(f"Delete {target} ({n} files) and reinstall? [y/N] ")
            if reply.strip().lower() not in ("y", "yes"):
                raise SystemExit("Aborted.")

        shutil.rmtree(target)

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        src,
        target,
        ignore=shutil.ignore_patterns("*.py", "__pycache__", "*.pyc"),
    )
    print(f"Installed skill to {target}")
    print("Start a new agent session to pick it up.")
    return target

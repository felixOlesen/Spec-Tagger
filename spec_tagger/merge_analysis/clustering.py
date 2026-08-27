"""clustering.py — turn a pairwise relatedness matrix into behaviour groups,
then derive labelled drift checkpoints from each group's composition and ordering.

The matrix measures TOPIC, not correctness: a high score means two commits concern
the same behaviour. Drift is read from what a group is MISSING (persistent drift)
and from the ORDER its artifacts arrived in (transient drift).
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 1. Clustering — connected components over the thresholded matrix
# ---------------------------------------------------------------------------


def build_groups(
    matrix: dict[tuple[str, str], dict[str, float]],
    all_commits: list[str],
    threshold: float = 0.05,
) -> list[set[str]]:
    """Commits linked by any score >= threshold form one behaviour group.

    Union-find rather than recursion: groups are small, and this avoids any
    depth concern on a long chain of weakly-linked commits.
    """
    parent = {c: c for c in all_commits}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path compression
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for (a, b), scores in matrix.items():
        if any(s >= threshold for s in scores.values()):
            union(a, b)

    groups: dict[str, set[str]] = {}
    for c in all_commits:
        groups.setdefault(find(c), set()).add(c)

    # Singletons are commits nothing else relates to — keep them, they are the
    # "src only, nothing follows" case, which is a real finding.
    return list(groups.values())


# ---------------------------------------------------------------------------
# 2. Composition and ordering
# ---------------------------------------------------------------------------

COMPOSITION_LABELS = {
    frozenset({"spec", "test", "src"}): (
        "complete",
        "Consistent at merge — control case",
    ),
    frozenset({"test", "src"}): (
        "undocumented",
        "Implemented and verified, never documented",
    ),
    frozenset({"spec", "src"}): ("unverified", "Implemented and documented, no test"),
    frozenset({"src"}): ("bare_implementation", "Neither documented nor verified"),
    frozenset({"spec", "test"}): (
        "retroactive",
        "Documents/verifies PRE-EXISTING behaviour — prior drift",
    ),
    frozenset({"spec"}): ("prose_only", "Spec changed alone — materiality judgement"),
    frozenset({"test"}): ("test_only", "Test changed alone"),
}


@dataclass
class Checkpoint:
    """A commit at which the expected drift state is known, because a LATER
    commit in the same group resolved it."""

    sha: str
    position: int
    present: set[str]
    missing: set[str]
    expected_finding: str


@dataclass
class BehaviourGroup:
    commits: list[str]  # chronological
    kinds_by_commit: dict[str, set[str]]
    composition: str = ""
    description: str = ""
    checkpoints: list[Checkpoint] = field(default_factory=list)

    @property
    def kinds(self) -> set[str]:
        return set().union(*self.kinds_by_commit.values())

    @property
    def is_staggered(self) -> bool:
        """Artifacts arrived in separate commits — the interesting case."""
        return len({frozenset(k) for k in self.kinds_by_commit.values()}) > 1


def analyse_group(
    commits: set[str],
    kinds_by_commit: dict[str, set[str]],
    chronological: list[str],
) -> BehaviourGroup:
    ordered = [c for c in chronological if c in commits]
    g = BehaviourGroup(
        commits=ordered,
        kinds_by_commit={c: kinds_by_commit[c] for c in ordered},
    )
    g.composition, g.description = COMPOSITION_LABELS.get(
        frozenset(g.kinds), ("other", "Unrecognised composition")
    )
    g.checkpoints = _checkpoints(g)
    return g


def _checkpoints(g: BehaviourGroup) -> list[Checkpoint]:
    """Walk the group forward. At each commit, whatever the group eventually
    contains but has not yet arrived is drift — and we know it is drift because
    a later commit in this same group supplies it."""
    eventual = g.kinds
    seen: set[str] = set()
    out: list[Checkpoint] = []

    for i, sha in enumerate(g.commits):
        seen |= g.kinds_by_commit[sha]
        missing = eventual - seen
        if not missing:
            break  # consistent from here on

        if "src" in seen and "test" in missing and "spec" in missing:
            expected = "uncovered_change: behaviour undocumented and untested"
        elif "src" in seen and "spec" in missing:
            expected = "uncovered_change: behaviour implemented but undocumented"
        elif "src" in seen and "test" in missing:
            expected = "coverage_gap: behaviour implemented but unverified"
        elif "spec" in seen and "src" in missing:
            expected = "spec describes behaviour not yet implemented"
        else:
            expected = f"incomplete: awaiting {', '.join(sorted(missing))}"

        out.append(Checkpoint(sha, i, set(seen), missing, expected))
    return out


# ---------------------------------------------------------------------------
# 3. Candidate selection
# ---------------------------------------------------------------------------


def rank_candidates(groups: list[BehaviourGroup]) -> list[BehaviourGroup]:
    """Prefer groups that give unambiguous, cheap-to-tag drift cases:
    * small          — fewer artifacts to tag, less ambiguity
    * staggered      — artifacts arrived separately, so checkpoints exist
    * retroactive    — strongest label: prior drift the project itself fixed
    """

    def score(g: BehaviourGroup) -> tuple:
        return (
            g.composition == "retroactive",  # gold signal first
            bool(g.checkpoints),  # then anything with checkpoints
            -len(g.commits),  # then smaller groups
        )

    return sorted(groups, key=score, reverse=True)


def report(groups: list[BehaviourGroup]) -> str:
    lines = []
    for i, g in enumerate(rank_candidates(groups), 1):
        if g.composition == "other":
            continue
        lines.append(f"--- group {i}: {g.composition} ({len(g.commits)} commits)")
        lines.append(f"    {g.description}")
        for sha in g.commits:
            kinds = ",".join(sorted(g.kinds_by_commit[sha]))
            lines.append(f"      {sha[:8]}  [{kinds}]")
        for cp in g.checkpoints:
            lines.append(
                f"    CHECKPOINT {cp.sha[:8]} (pos {cp.position}): "
                f"have {sorted(cp.present)}, missing {sorted(cp.missing)}"
            )
            lines.append(f"      expect -> {cp.expected_finding}")
        lines.append("")
    return "\n".join(lines)

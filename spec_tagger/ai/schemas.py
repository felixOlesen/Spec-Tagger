from pydantic import BaseModel, Field
from typing import Literal


class FailureDiagnostic(BaseModel):
    """Why did a spec-linked test fail? Code, test, or spec at fault."""

    cause: Literal["code_wrong", "test_wrong", "spec_wrong", "unclear"] = Field(
        description=(
            "code_wrong: an unintended regression — spec and test are both still "
            "correct. test_wrong: behaviour changed deliberately and the spec "
            "already reflects it, but the test was not updated. spec_wrong: "
            "behaviour changed deliberately and correctly, and the prose describes "
            "older intent. unclear: the evidence does not distinguish between "
            "these — a legitimate answer, not a failure."
        )
    )
    confidence: int = Field(
        ge=0,
        le=100,
        description=(
            "How strongly the evidence supports this cause. 80+ when the commit "
            "messages, diff, spec and assertion all align on one cause; 60-79 when "
            "it leans one way but an alternative remains plausible; below 60 means "
            "you are guessing — prefer 'unclear'. Do not inflate."
        ),
    )
    reasoning: str = Field(
        description=(
            "Two to four sentences. State which artefacts agree with each other, "
            "which one disagrees, and why that points to your chosen cause."
        )
    )
    evidence: list[str] = Field(
        description=(
            "Specific quoted or referenced items from the inputs that support the "
            "verdict — a commit message, a changed line, the failing assertion. "
            "Point at real content, not general impressions."
        ),
    )
    suggested_edit: str | None = Field(
        description=(
            "The minimal replacement text that resolves the disagreement. Provide "
            "ONLY for test_wrong or spec_wrong. Never for code_wrong — a probable "
            "regression needs human investigation, not an automated fix. Never "
            "weaken or delete an assertion to make a test pass."
        ),
    )


class SemanticDrift(BaseModel):
    """Does a passing test still verify what its spec prose claims?"""

    drifted: bool = Field(
        description=(
            "True if the test no longer verifies what the prose describes, even "
            "though it passes. Don't just check the assertions but the entire diff, spec content, and test content, if the process is different, it might indicate that drift has occurred."
            "False if the test still genuinely checks the "
            "described behaviour."
            "Focus less on aesthetic changes such as changed variable names, when the code does the exact same thing."
        )
    )
    confidence: int = Field(
        ge=0, le=100, description="Certainty in this judgement, 0-100."
    )
    what_prose_claims: str = Field(
        description="In one or two sentences, the behaviour the spec prose describes."
    )
    what_test_verifies: str = Field(
        description=(
            "In one or two sentences, the behaviour the test actually asserts. State this "
            "from the assertions themselves, not just from the test's name. Also make sure to check the content of the test when available, to see if there's any drift in the process, even if the outcome is the same."
        )
    )
    reasoning: str = Field(
        description="Why the spec prose and the tests do or do not describe the behabiour."
    )
    suggested_change: str = Field(
        description="If you believe there is drift present, provide an educated suggestion about what needs to change to fix the semantic drift, provide a maximum of 4 lines as a snapshot of what the solution can look like, it doesn't have to be complete, just give the developer an idea of how it can be fixed."
    )


CoverageState = Literal[
    "uncovered",  # no spec describes it AND no test verifies it
    "spec_only",  # a spec describes it but no test verifies it
    "test_only",  # a test verifies it but no spec describes it
]

Significance = Literal["behavioural", "internal", "cosmetic"]


class UncoveredChange(BaseModel):
    """One behavioural change in the implementation that specs and tests miss."""

    behaviour: str = Field(
        description=(
            "What the changed code now does, stated as observable behaviour a user "
            "could notice not literally describing what the code does, but what changes"
            "to the behaviour of the software appear from the code changes. Determine whether or not"
            "the change should be an actionable change based on the content of the change"
            "Understand that the code you're looking at is a git log of the changes and may not describe the full picture of the change."
            "Other code might be present that is covered by the tests that have been run, while the lines you see might be an unexplored branch."
        )
    )
    files: list[str] = Field(
        description="The changed file paths this behaviour lives in, as given in the diff."
    )
    coverage_state: CoverageState = Field(
        description=(
            "uncovered: neither a spec item describes this behaviour nor a test "
            "verifies it. spec_only: a spec item describes it but no test verifies "
            "it. test_only: a test verifies it but no spec item describes it. Judge "
            "from the spec items and tags supplied in the input — if you cannot see "
            "any spec or test covering it, that is 'uncovered'."
        )
    )
    significance: Significance = Field(
        description=(
            "behavioural: changes what the system does from the outside — new rules, "
            "changed outputs, new error paths, altered defaults. internal: "
            "refactoring, restructuring, or performance work with no observable "
            "change. cosmetic: formatting, comments, renames. Only 'behavioural' "
            "changes genuinely need a spec and a test; report the others so a human "
            "can confirm, but do not treat them as gaps."
        )
    )
    evidence: list[str] = Field(
        description=(
            "Specific lines or hunks from the diff that establish this behaviour. "
            "Quote or reference real content so a reviewer can verify the claim."
        ),
    )
    matches_stated_intent: bool | None = Field(
        description=(
            "True if the commit messages or PR description mention this change; "
            "false if the change is present in the diff but unmentioned; null if "
            "no intent statements were supplied. An unmentioned behavioural change "
            "is worth flagging on its own — it may be unintended."
        ),
    )
    suggested_spec: str | None = Field(
        description=(
            "For 'uncovered' or 'test_only' behavioural changes, a one-or-two "
            "sentence draft spec item describing this behaviour, written at the "
            "same altitude as the existing spec items. Null otherwise. Do not "
            "invent a tag or revision number."
        ),
    )
    suggested_test: str | None = Field(
        description=(
            "For uncovered behavioral changes, suggest a test function that the developer could"
            "could implement in the test code to cover the change. Try to include as many real functions as you can"
            "but also feel free to use pseudo code or comments to indicate steps that you cannot find direct code for"
            "when going through the test steps. Write the test in the programming language of the uncovered change you've been given."
            "If you are completely unable to write code for the test, then write a 2 to 3 sentence description of what you want the test to check."
        ),
    )
    confidence: int = Field(
        ge=0,
        le=100,
        description=(
            "How certain you are that this is a real, distinct behavioural change "
            "that the supplied specs and tests do not cover. Below 60 means you are "
            "guessing — omit the item rather than reporting it. Do not inflate: a "
            "list padded with weak findings trains reviewers to ignore the report."
        ),
    )


class CoverageGapReport(BaseModel):
    """The full result of scanning one PR's implementation changes."""

    changes: list[UncoveredChange] = Field(
        description=(
            "One entry per distinct behavioural change. Merge related edits that "
            "serve a single behaviour into one entry rather than listing each hunk. "
            "Return an empty list if every change is internal, cosmetic, or already "
            "covered — an empty list is a valid and useful answer."
        ),
    )
    diff_fully_reviewed: bool = Field(
        description=(
            "True if you were able to consider the entire diff supplied. False if it "
            "was large enough that you may have missed changes — say so rather than "
            "implying completeness you cannot guarantee."
        )
    )
    summary: str = Field(
        description=(
            "Two or three sentences: what this PR changes behaviourally overall, and "
            "whether the specs and tests keep pace with it."
        )
    )


InvalidTagCase = Literal[
    "DUPLICATE_SPEC_TAG",
    "NO_TEST_TAG_FOR_SPEC_TAG",
    "NO_FUNCTION_FOR_TEST_TAG",
    "NO_SPEC_TAG_FOR_TEST_TAG",
    "TAG_REVISION_MISMATCH",
]

ResolutionAction = Literal[
    "rename_tag",  # give this tag a new name (duplicate resolution)
    "keep_tag",  # this one is correct; others change around it
    "relocate_tag",  # the tag is in the wrong place — move it
    "remove_tag",  # the tag should not exist
    "bump_revision",  # raise a lagging revision to match the latest
    "update_content",  # the spec prose or test needs changing, not the tag
    "add_test",  # write a new test to satisfy this tag
    "add_spec_item",  # write a new spec item for this test
    "needs_human",  # the evidence does not support a confident resolution
]


class TagSuggestion(BaseModel):
    """A proposed spec tag for a test that currently has none."""

    test_file: str = Field(description="Path to the test file, as given in the input.")
    test_name: str = Field(description="Name of the test function or example.")
    spec_tag: str = Field(
        description=(
            "The EXISTING spec tag this test verifies, in type~name~revision form. "
            "Only propose a tag that appears in the supplied spec items — never "
            "invent one."
        )
    )
    confidence: int = Field(
        ge=0,
        le=100,
        description=(
            "How certain this test verifies that spec item. Match on BEHAVIOUR, not "
            "shared vocabulary: a test named test_sum that verifies the addition "
            "story is a match; a test that merely repeats the same words while "
            "verifying something else is not. If no spec item genuinely matches, do "
            "not propose one — an uncovered spec item is a real finding, and "
            "inventing a link reports coverage that does not exist. Treat anything "
            "below 70 as needing explicit human review and say so."
        ),
    )
    reasoning: str = Field(
        description="One sentence on why this test's behaviour matches this spec item."
    )


class InvalidTagResolution(BaseModel):
    """A proposed resolution for one tag the crawler flagged as invalid."""

    tag: str = Field(
        description="The invalid tag, exactly as it appears in the source."
    )
    location: str = Field(description="file:line where this tag sits.")
    case: InvalidTagCase = Field(
        description=(
            "The kind of invalidity, as determined by the crawler. "
            "DUPLICATE_SPEC_TAG: the same tag names more than one spec item. "
            "NO_TEST_TAG_FOR_SPEC_TAG: a spec tag has no test tags assigned to it. "
            "NO_FUNCTION_FOR_TEST_TAG: a test tag does not bind to any test function. "
            "NO_SPEC_TAG_FOR_TEST_TAG: a test tag references a spec tag that does not "
            "exist. TAG_REVISION_MISMATCH: tags for the same item carry different "
            "revision numbers."
        )
    )
    action: ResolutionAction = Field(
        description=(
            "What should be done. Choose per case:\n"
            "DUPLICATE_SPEC_TAG — identify which spec item the tag fits BEST and mark "
            "that one 'keep_tag'; every other duplicate gets 'rename_tag' with a new "
            "name in proposed_value.\n"
            "NO_TEST_TAG_FOR_SPEC_TAG — 'add_test' if no existing test covers the "
            "behaviour, or 'relocate_tag' if a suitable test exists and simply lacks "
            "the tag (name it in proposed_value).\n"
            "NO_FUNCTION_FOR_TEST_TAG — the tag is misplaced: 'relocate_tag' if the "
            "intended test is identifiable, 'remove_tag' if it is stale, or 'add_test' "
            "if the behaviour genuinely needs a new test.\n"
            "NO_SPEC_TAG_FOR_TEST_TAG — 'add_spec_item' to write the missing spec "
            "portion, or 'rename_tag' if the reference is a typo for an existing item.\n"
            "TAG_REVISION_MISMATCH — inspect the content behind the lower revision "
            "against the latest. If it already reflects the newer meaning, "
            "'bump_revision'. If it does not, 'update_content' and say what must "
            "change.\n"
            "Use 'needs_human' whenever the evidence does not support a confident "
            "choice — that is a legitimate answer, not a failure."
        )
    )
    proposed_value: str | None = Field(
        description=(
            "The concrete replacement the action calls for: the new tag name for "
            "'rename_tag', the target file:line for 'relocate_tag', the new revision "
            "for 'bump_revision', the draft prose for 'add_spec_item'. Null when the "
            "action needs no value, or when you cannot state it precisely."
        ),
    )
    affects: list[str] = Field(
        description=(
            "Other tags or locations this resolution would also change — the sibling "
            "duplicates being renamed, or the other tags of the same revision that "
            "must move together. A reviewer needs to see the full blast radius."
        ),
    )
    confidence: int = Field(
        ge=0,
        le=100,
        description=(
            "Certainty in this resolution. Below 60 means you are guessing — prefer "
            "'needs_human'. Do not inflate: an inflated score sends a reviewer to "
            "accept a change they should have questioned."
        ),
    )
    reasoning: str = Field(
        description=(
            "One to three sentences: what the evidence shows and why this action "
            "follows from it."
        )
    )
    requires_content_change: bool = Field(
        description=(
            "True if resolving this needs an edit to spec prose or test logic rather "
            "than to a tag alone. Those edits are never applied automatically — they "
            "change the artefacts being measured — so flag them for human decision."
        ),
    )

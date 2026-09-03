from pydantic import BaseModel, Field
from typing import Literal


class SemanticDrift(BaseModel):
    """Does a passing test still verify what its spec prose claims?"""

    drifted: bool = Field(
        description=(
            "True if the test no longer verifies what the prose describes, even "
            "though it passes. Don't just check the assertions but the entire diff, spec content, and test content, if the process is different, it might indicate that drift has occurred."
            "False if the test still genuinely checks the described behaviour even if some purely cosmetic differences are present."
            "Focus less on aesthetic changes such as changed or different variable names, when the code functions in the same way still."
        )
    )
    confidence: int = Field(
        ge=0, le=100, description="Certainty in this judgement, 0-100."
    )
    what_prose_claims: str = Field(
        description="In at most 2 sentences, the behaviour the spec content describes."
    )
    what_test_verifies: str = Field(
        description=(
            "In at most 2 sentences, the behaviour the test actually asserts. State this "
            "from the assertions themselves and the test content, not just from the test's name. Also make sure to"
            "check the content of the test when available, to see if there's any drift in the process, even if the outcome is the same."
        )
    )
    reasoning: str = Field(
        description="Why the spec prose and the tests do or do not describe the behaviour."
    )
    suggested_change: str = Field(
        description="If you believe there is drift present, provide an educated suggestion about what needs to change to fix the semantic drift, provide a maximum of 4 lines as a snapshot of what the solution can look like, it doesn't have to be complete, just give the developer an idea of how it can be fixed."
    )


Significance = Literal["behavioural", "cosmetic"]


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
        description="The changed file paths this change is present in, as given in the diff."
    )

    significance: Significance = Field(
        description=(
            "behavioural: describes changes that impact how the software functions, not just an aesthetic change that or a minor re-factor."
            "cosmetic: describes the types of changes that are simply stylistic, comments, or renamings of things, no changes required for this type."
            "Only behavioural changes need a suggestion spec and test, report cosmetic changes for human review as well."
        )
    )
    evidence: list[str] = Field(
        description=(
            "Specific lines or sections from the diff that establish this behaviour. "
            "Quote or reference real content so a reviewer can verify the claim."
        ),
    )
    suggested_spec: str | None = Field(
        description=(
            "For uncovered behavioural change, a few sentences giving succinct behavioural description of what"
            "software behaviour the code undertakes. Written in a way such that a non-technical person could"
            "understand it and given in the form of natural language. Do not add a tag to this, leave that for a human to do."
        ),
    )
    suggested_test: str | None = Field(
        description=(
            "For uncovered behavioural changes, suggest a test function that the developer could implement"
            "in the test code to cover the change. Try to include as many real functions as you can"
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

from pathlib import Path
import os
from dotenv import load_dotenv
from spec_tagger.ai.anthropic_controller import AnthropicController
from spec_tagger.ai.prompt_construction import PromptConstructor
from spec_tagger.ai.schemas import SemanticDrift
from spec_tagger.spec_review.context_aggregator import ContextAggregator
from spec_tagger.spec_review.result_triage import ProblemType, ResultTriage
from spec_tagger.ai.litellm_controller import LiteLLMController


def validate_args(args):
    if not args.report_input:
        raise ValueError(f"report_input '{args.report_input}' is none")
    if args.report_input and not Path.is_file(args.report_input):
        raise ValueError(f"report_iput '{args.report_input}' file does not exist")


def run(args):
    validate_args(args)
    # Aggregate Context
    aggregator = ContextAggregator(args.report_input)
    collected_context = aggregator.get_all_context()
    git_global_context = aggregator.git_context_data
    # Classify Problem
    triage = ResultTriage(collected_context)
    solutions = triage.filter_results()
    for solution in solutions:
        solution.display_data()
    # Construct Prompt OR NO-AI Method
    if not args.no_ai:
        prompt_constructor = PromptConstructor(solutions, git_global_context)
        prompts = prompt_constructor.construct_prompt_list()
        ai_controller = LiteLLMController(
            args.model_provider, args.model_name, args.rate_limit
        )
        findings = []
        for prompt in prompts:
            response, usage_info, cost_usd = ai_controller.send_prompt(
                prompt.schema,
                prompt.context_evidence,
                prompt.system_prompt,
            )
            finding = {
                "problem_type": prompt.problem_type,
                "response": response,
            }

            findings.append(finding)
            ai_controller.parse_response(response, usage_info, cost_usd)
            ai_controller.show_total_session_token_usage()
            write_findings_markdown(findings)

    # Prepare output suggestion
    # Feed into workflow for PR OR Print to STDOUT


def write_findings_markdown(findings):
    md = render(findings)
    with open("spectagger_findings.md", "w") as fh:
        fh.write(md)

    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a") as fh:
            fh.write(md + "\n")


PRIORITY_MIN_CONFIDENCE = 70


def render(findings) -> str:
    """findings: list of {"problem_type": ProblemType, "response": <schema>}"""
    # A non-drifted result is a confirmation, not a finding — drop it entirely.
    drifts = []
    changes = []
    for finding in findings:
        if finding["problem_type"] == ProblemType.IMPLEMENTATION_CHANGE_NOT_COVERED:
            changes.append(finding["response"])
        elif (
            finding["problem_type"] == ProblemType.PASSED_BUT_CHANGED
            and finding["response"].drifted
        ):
            drifts.append(finding["response"])

    # Only behavioural changes are genuine gaps; internal/cosmetic are noise.
    priority_changes = [
        c
        for c in changes
        if c.significance == "behavioural"
        and c.coverage_state in ("uncovered", "spec_only")
        and c.confidence >= PRIORITY_MIN_CONFIDENCE
    ]
    priority_drifts = [d for d in drifts if d.confidence >= PRIORITY_MIN_CONFIDENCE]
    rest_changes = [c for c in changes if c not in priority_changes]
    rest_drifts = [d for d in drifts if d not in priority_drifts]

    out = ["## Spec review", ""]

    if not priority_drifts and not priority_changes:
        out += [
            "No high-confidence semantic drift or uncovered behavioural changes found.",
            "",
        ]

    if priority_drifts:
        out += [f"### Semantic drift ({len(priority_drifts)})", ""]
        for d in priority_drifts:
            out += [
                f"**Confidence {d.confidence}**",
                "",
                f"- Spec claims: {d.what_prose_claims}",
                f"- Test verifies: {d.what_test_verifies}",
                "",
                d.reasoning,
                "",
            ]

    if priority_changes:
        out += [f"### Uncovered behavioural changes ({len(priority_changes)})", ""]
        for c in priority_changes:
            files = ", ".join(f"`{f}`" for f in c.files)
            out += [
                f"**{c.behaviour}** · confidence {c.confidence}",
                f"{files} — {c.coverage_state.replace('_', ' ')}",
                "",
            ]
            if c.matches_stated_intent is False:
                out += [
                    "> Not mentioned in any commit message or the PR "
                    "description — worth confirming this was intended.",
                    "",
                ]
            if c.suggested_spec:
                out += ["Suggested spec item:", "", f"> {c.suggested_spec}", ""]
            if c.evidence:
                snippet = "\n".join(l for l in c.evidence if l.strip())
                out += [
                    "<details><summary>Evidence</summary>",
                    "",
                    "```",
                    snippet,
                    "```",
                    "",
                    "</details>",
                    "",
                ]

    rest_total = len(rest_changes) + len(rest_drifts)
    if rest_total:
        out += [
            "<details>",
            f"<summary>Other findings ({rest_total})</summary>",
            "",
        ]  # blank line required
        for d in rest_drifts:
            out.append(
                f"- **Semantic drift** — possible drift, confidence {d.confidence}"
            )
        for c in rest_changes:
            out.append(
                f"- **{c.behaviour}** — {c.significance}, "
                f"{c.coverage_state.replace('_', ' ')}, confidence {c.confidence}"
            )
        out += ["", "</details>"]

    return "\n".join(out)

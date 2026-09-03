from json import load
from pathlib import Path
import os

from tqdm import tqdm
from spec_tagger.spec_review.context_aggregator import ContextAggregator
from spec_tagger.spec_review.result_triage import ProblemType, ResultTriage
from spec_tagger.spec_review.solution import Solution


def validate_args(args):
    """Validates all args for the spec-review sub-command that are passed in by the user"""
    if not args.report_input:
        raise ValueError(f"report_input '{args.report_input}' is none")
    if args.report_input and not Path.is_file(Path(args.report_input)):
        raise ValueError(f"report_iput '{args.report_input}' file does not exist")
    if not args.src_dir:
        raise ValueError(f"src_dir '{args.src_dir}' is none")
    if args.src_dir and not Path.is_dir(Path(args.src_dir)):
        raise ValueError(f"src_dir '{args.src_dir}' folder does not exist")


def run(args):
    validate_args(args)
    # Aggregate Context
    aggregator = ContextAggregator(args.report_input, args.base, args.head)
    collected_context = aggregator.get_all_context()
    git_global_context = aggregator.git_context_data

    for key, context_item in collected_context["report"].items():
        print(key)
        if not context_item:
            print(key)
    # Classify Problem
    triage = ResultTriage(
        collected_context,
        args.src_dir,
        no_ai=args.no_ai,
        semantic_drift_included=args.include_semantic_drift_review,
        unlinked_tests_included=args.include_unlinked_tests_in_report,
        failed_tests_included=args.include_failed_tests_in_report,
        invalid_tags_included=args.include_invalid_tags_in_report,
        uncovered_implementation_included=args.include_uncovered_implementation_review,
    )
    solutions = triage.filter_results()
    findings = parse_non_ai_findings(solutions)
    if findings:
        print(f"Non-AI Cases Found: {len(findings)}")
    # Construct Prompt OR NO-AI Method
    if not args.no_ai:
        from spec_tagger.ai.prompt_construction import PromptConstructor
        from spec_tagger.ai.litellm_controller import LiteLLMController

        prompt_constructor = PromptConstructor(solutions, git_global_context)
        prompts = prompt_constructor.construct_prompt_list()
        ai_controller = LiteLLMController(
            args.model_provider, args.model_name, args.rate_limit
        )
        if prompts:
            print(f"LLM-Required Cases Discovered in Report: {len(prompts)}")
        for prompt in prompts:
            if args.verbose_review:
                prompt.pretty_print_prompt()
            else:
                print(f"Running prompt with type: {prompt.problem_type}")
            response, usage_info, cost_usd = ai_controller.send_prompt(
                prompt.schema,
                prompt.context_evidence,
                prompt.system_prompt,
            )
            finding = {
                "problem_type": prompt.problem_type,
                "response": response,
            }
            if prompt.problem_type == ProblemType.PASSED_BUT_CHANGED:
                print(f"Semantic Drift Result: {response.drifted}")

            findings.append(finding)
            if args.verbose_review:
                ai_controller.print_response(response, usage_info, cost_usd)
            ai_controller.show_total_session_token_usage()

    write_findings_markdown(findings)


def parse_non_ai_findings(solutions: list[Solution]) -> list[dict]:
    result = []
    for solution in solutions:
        if not solution.ai_usage_recommended:
            result.append(
                {
                    "problem_type": solution.problem_type,
                    "response": solution.construct_non_ai_response(),
                }
            )
    return result


def write_findings_markdown(findings):
    """Write findings markdown saves the rendered results of the findings into
    a markdown file of the name spectagger_findings.md"""
    md = render(findings)
    with open("spectagger_findings.md", "w") as fh:
        fh.write(md)
        print("Report written to ./spectagger_findings.md")

    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a") as fh:
            fh.write(md + "\n")


def render(findings: list[dict]) -> str:
    """Render looks through the list of findings post-llm run and constructs a markdown
    string that presents the LLM findings.
    """
    PRIORITY_MIN_CONFIDENCE = 70
    drifts = []
    changes = []
    non_ai_suggestions = []
    for finding in findings:
        if finding["problem_type"] == ProblemType.IMPLEMENTATION_CHANGE_NOT_COVERED:
            changes.append(finding["response"])
        elif (
            finding["problem_type"] == ProblemType.PASSED_BUT_CHANGED
            and finding["response"].drifted
        ):
            drifts.append(finding["response"])
        elif finding["problem_type"] in (
            ProblemType.INVALID_TAG,
            ProblemType.TEST_FAILURE,
            ProblemType.TEST_ERROR,
            ProblemType.MISSED_FILE,
            ProblemType.MISSED_TEST,
        ):
            non_ai_suggestions.append(finding)

    priority_changes = [
        change
        for change in changes
        if change.significance == "behavioural"
        and change.confidence >= PRIORITY_MIN_CONFIDENCE
    ]
    priority_drifts = [d for d in drifts if d.confidence >= PRIORITY_MIN_CONFIDENCE]
    rest_changes = [c for c in changes if c not in priority_changes]
    rest_drifts = [d for d in drifts if d not in priority_drifts]

    out = ["", "## Spec review", ""]

    if not priority_drifts and not priority_changes:
        out += [
            "No high-confidence semantic drift or uncovered behavioural changes found.",
            "",
        ]

    if priority_drifts:
        out += [f"### Semantic drift ({len(priority_drifts)})", ""]
        for drift in priority_drifts:
            out += [
                f"**Confidence {drift.confidence}**",
                "",
                f"- Spec describes: {drift.what_prose_claims}",
                f"- Test describes: {drift.what_test_verifies}",
                "",
                drift.reasoning,
                "",
            ]
            if drift.suggested_change:
                out += [
                    "Suggested change:",
                    "",
                    "```",
                    drift.suggested_change,
                    "```",
                    "",
                ]

    if priority_changes:
        out += [f"### Uncovered behavioural changes ({len(priority_changes)})", ""]
        for change in priority_changes:
            files = ", ".join(f"`{f}`" for f in change.files)
            out += [
                f"**{change.behaviour}** · confidence {change.confidence}",
                f"{files}",
                "",
            ]
            if change.suggested_spec:
                out += ["Suggested spec item:", "", f"> {change.suggested_spec}", ""]
            if change.suggested_test:
                out += ["Suggested test:", "", "```", change.suggested_test, "```", ""]
            if change.evidence:
                snippet = "\n".join(l for l in change.evidence if l.strip())
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
        ]
        for drift in rest_drifts:
            out.append(f"- **Semantic drift**, confidence {drift.confidence}")
        for change in rest_changes:
            out.append(
                f"- **{change.behaviour}** — {change.significance}, "
                f"confidence {change.confidence}"
            )
        out += ["", "</details>"]

    if non_ai_suggestions:
        out += ["", "## Non-Ai Suggestions", ""]
        for suggestion in non_ai_suggestions:
            out += ["", f"{suggestion['response']}", ""]

    return "\n".join(out)

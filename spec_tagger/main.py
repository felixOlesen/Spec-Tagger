import argparse
from spec_tagger.tag_test import orchestrator as tag_test_orchestrator
from spec_tagger.spec_review import orchestrator as review_orchestrator
import spec_tagger.agent_skill.skill_installer as skill_installer


def main():
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(dest="command")
    skill_parser = sub_parsers.add_parser("install-skill")
    spec_review_parser = sub_parsers.add_parser("spec-review")

    # SKILL INSTALL ARGS
    skill_parser.add_argument(
        "--destination",
        help="The destination that you want the spectagger skill folder to be copied to. E.g. ~/.claude/skills for claude code.",
        required=True,
    )
    skill_parser.add_argument(
        "--force",
        help="Forces the installer script to overwrite any pre-existing installations of the spectagger skill.",
        action="store_true",
    )
    skill_parser.add_argument(
        "--install_dry_run",
        help="Prints a where the file would be installed without actually installing it, good for testing.",
        action="store_true",
    )

    # SPEC REVIEW ARGS
    spec_review_parser.add_argument(
        "--report_input",
        help="Tells the program where the report.json is for analysing the test results from a spectagger run.",
        default="report",
    )
    spec_review_parser.add_argument(
        "--model_provider",
        help="The provider route used in litellm to indicate a valid provider, for example 'gemini', 'nvidia_nim', 'openrouter', etc.",
        default="gemini",
    )
    spec_review_parser.add_argument(
        "--model_name",
        help="The model name is the name of the specific model that is valid for the provider that you are using, for example: 'gemini-3.5-flash'.",
        default="gemini-3.5-flash",
    )
    spec_review_parser.add_argument(
        "--rate_limit",
        help="This needs to be an integer describing the maximum responses per minute that are allowed for a specific endpoint, please refer to your API documentation for this.",
        default=10,
    )
    spec_review_parser.add_argument(
        "--no_ai",
        help="Runs the Spec-Reivew without AI tooling in case it's not available to the user.",
        action="store_true",
    )
    spec_review_parser.add_argument(
        "--include_semantic_drift_review",
        help="Tells the tool, that you want to specifically include semantic drift checking for changed files located in git diffs and logs, if no specific review is requested, all will be run.",
        action="store_true",
    )
    spec_review_parser.add_argument(
        "--include_failure_diagnostic_review",
        help="Tells the tool, that you want to specifically include reviews for improvements to either the spec, the tests or the implementation code in the case that any related tests fail, if no specific review is requested, all will be run.",
        action="store_true",
    )
    spec_review_parser.add_argument(
        "--include_tag_suggestion_review",
        help="Tells the tool, that you want to specifically include new tag suggestions for un-tagged test files and test cases, if no specific review is requested, all will be run.",
        action="store_true",
    )
    spec_review_parser.add_argument(
        "--include_invalid_tag_review",
        help="Tells the tool, that you want to specifically include the review of cases of invalid tags, if no specific review is requested, all will be run.",
        action="store_true",
    )
    spec_review_parser.add_argument(
        "--include_entire_diff_review",
        help="Tells the tool, that you want to specifically include the entire diff in the 'un-covered implementation file checking' stage instead of just looking at changed files that haven't been covered at all by the current testing in place, WARNING: This could result in very large token usage if your git diff is large, please double check that the usage will be sufficient for your needs.",
        action="store_true",
    )
    spec_review_parser.add_argument(
        "--src_dir",
        help="Directory where your application source code is located, allows for the tool to ignore non-implementation files that are present in git.",
    )

    # CORE TOOL ARGS
    parser.add_argument(
        "--target_spec",
        default="features",
        help="Target dir/file/tag/list of files to read through",
    )
    parser.add_argument(
        "--spec_file_extensions",
        default=None,
        help="Comma-separated list of allowed spec file extensions",
    )
    parser.add_argument(
        "--tag_check",
        action="store_true",
        help="Focuses entirely on identifying invalid tags, preventing the tool from continuing on to running tests.",
    )
    parser.add_argument(
        "--target_tag",
        default=None,
        help="Specify a target tag for the crawler to look for and run tests against, works with specified files in taret_spec as well.",
    )

    parser.add_argument(
        "--test_dir",
        default="tests",
        help="Root directory for all test files that need to be crawled through",
    )
    parser.add_argument(
        "--test_command", help="Command to run the test, example: 'pytest {tests}'"
    )
    parser.add_argument(
        "--test_format",
        default="{file}::{name}",
        help="How a single test is addressed on the CLI. Placeholders: {file} = test file path, {name} = test function name.",
    )
    parser.add_argument(
        "--test_framework",
        help="Providing a test framework string will override the detection function for a minor speed up, if no framework is found, the tool will resort to file-based testing",
    )

    parser.add_argument(
        "--one_by_one",
        action="store_true",
        help="Use in case you want to run each test one-by-one, CAUTION: slows down testing significantly due to multiple subprocess calls.",
    )
    parser.add_argument(
        "--test_join",
        default=None,
        help='If set, join all test targets with this separator into ONE argument (e.g. "|" for go test -run) instead of passing them separately.',
    )
    parser.add_argument(
        "--test_extensions",
        default=None,
        help="Comma-separated list of allowed test file extensions",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="test the spec links without running the test code.",
    )
    parser.add_argument("--report", help="Generate a report", action="store_true")
    parser.add_argument(
        "--report_output", default=None, help="Directory to output the report"
    )
    parser.add_argument(
        "--report_type",
        default="json",
        help="Type of report to generate",
        choices=["json", "html", "stdout"],
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enables verbose printing"
    )

    parser.add_argument(
        "--coverage_report_path",
        default=None,
        help="Path to be provided by the user for where the coverage output report is being generated.",
    )

    parser.add_argument(
        "--coverage_library",
        default=None,
        help="The specific coverage library to parse a report for.",
        choices=["python.coverage", "ruby.simplecov"],
    )

    args = parser.parse_args()
    if args.verbose:
        print(f"Arguments: {args}")

    match args.command:
        case "install-skill":
            print("Install Skill Invoked")
            skill_installer.install_skill(
                args.destination, args.force, args.install_dry_run
            )
            return
        case "spec-review":
            print("Spec-Reivew command invoked")
            return review_orchestrator.run(args=args)
        case _:
            print("No command, running core tool...")
            return tag_test_orchestrator.run(args)


if __name__ == "__main__":
    main()

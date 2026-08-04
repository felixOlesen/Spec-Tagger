import argparse
from spec_tagger.tag_test import orchestrator as tag_test_orchestrator
import spec_tagger.agent_skill.skill_installer as skill_installer


def main():
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(dest="command")
    skill_parser = sub_parsers.add_parser("install-skill")
    ci_parser = sub_parsers.add_parser("ci")

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

    # CORE TOOL Args
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
        "--report_output", default="report", help="Directory to output the report"
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
    args = parser.parse_args()
    print(f"Arguments: {args}")

    match args.command:
        case "install-skill":
            print("Install Skill Invoked")
            skill_installer.install_skill(
                args.destination, args.force, args.install_dry_run
            )
            return
        case "ci":
            print("CI command invoked")
            return
        case _:
            print("No command, running core tool...")
            return tag_test_orchestrator.run(args)


if __name__ == "__main__":
    main()

import argparse
import os
from spec_tagger.spec_test_linker import Linker
from spec_tagger.test_runner import Runner
from spec_tagger.report_generation import Generator
from spec_tagger.spec_test_crawler import SpecCrawler, TestCrawler
from spec_tagger.language_patterns import detect_framework, framework_support_check


def validate_args(args):
    if not args.test_command:
        raise ValueError("test_command is required")
    if args.report and not args.report_output:
        raise ValueError("report_output is required when report is enabled")
    if args.report and args.report_type not in ["json", "html", "stdout"]:
        raise ValueError("Invalid report_type. Must be one of: json, html, stdout")
    if args.report and not os.path.isdir(args.report_output):
        raise ValueError(
            f"report_output '{args.report_output}' is not a valid directory"
        )
    if args.target_spec and not os.path.exists(args.target_spec):
        raise ValueError(f"target_spec '{args.target_spec}' does not exist")
    if args.test_dir and not os.path.exists(args.test_dir):
        raise ValueError(f"test_dir '{args.test_dir}' does not exist")


def main():
    parser = argparse.ArgumentParser()
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

    validate_args(args)
    print(f"Arguments: {args}")
    spec_crawler = SpecCrawler(
        verbose=args.verbose,
        spec_dir=args.target_spec,
        enabled_extensions=set(args.spec_file_extensions.split(","))
        if args.spec_file_extensions
        else None,
    )
    spec_tag_data = spec_crawler.run()
    fw_existence = True
    if args.test_framework:
        fw_existence = framework_support_check(args.test_framework)
    else:
        framework, matches = detect_framework(args.test_command)
        if not framework:
            print(
                "Warning, no framework was detectable from your test command, please specify one with the '--test_framework' argument."
            )
            print("Continuing at file-level test granularity")
            fw_existence = False
        else:
            print(f"Framework found: {framework}")
            if len(matches) > 1:
                print(f"Other matches found as well:\n{matches}")

    test_crawler = TestCrawler(
        verbose=args.verbose,
        test_dir=args.test_dir,
        enabled_extensions=set(args.test_extensions.split(","))
        if args.test_extensions
        else None,
        framework=fw_existence,
    )
    test_tag_data = test_crawler.run()

    linker = Linker(
        spec_data=spec_tag_data, test_data=test_tag_data, verbose=args.verbose
    )
    linked_data = linker.link_data()
    links = None
    invalid_tags = None
    if linked_data:
        links, invalid_tags = linked_data

    if args.verbose:
        linker.display_data()

    runner = Runner(
        test_run_command=args.test_command,
        test_format=args.test_format,
        test_join=args.test_join,
        linked_tags=links,
        one_by_one=args.one_by_one,
        verbose=args.verbose,
    )
    test_results = runner.run_tests(args.dry_run)

    if args.report and not args.dry_run:
        generator = Generator(
            report_output_dir=args.report_output,
            report_type=args.report_type,
            test_output=test_results,
            invalid_tags=invalid_tags,
            successful_links=links,
            verbose=args.verbose,
        )
        generator.generate_report()


if __name__ == "__main__":
    main()

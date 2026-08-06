import os
from spec_tagger.tag_test.spec_test_linker import Linker
from spec_tagger.tag_test.test_runner import Runner
from spec_tagger.tag_test.report_generation import Generator
from spec_tagger.tag_test.spec_test_crawler import TAG_PATTERN, SpecCrawler, TestCrawler
from spec_tagger.tag_test.language_patterns import (
    detect_framework,
    framework_support_check,
)
import re


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

    tag_regex = re.compile(TAG_PATTERN)
    if args.target_tag:
        m = tag_regex.search(args.target_tag)
        if not m:
            raise ValueError(
                f"target_tag provided: {args.target_tag}, doesn't match the format feat/story/step~name~revision_number"
            )

    if not args.target_spec:
        raise ValueError("target_spec value found to be null on validation.")

    target_spec = args.target_spec.split(",")

    for target in target_spec:
        if target and not os.path.exists(target):
            raise ValueError(f"target_spec '{target}' does not exist")

    if args.test_dir and not os.path.exists(args.test_dir):
        raise ValueError(f"test_dir '{args.test_dir}' does not exist")

    if args.test_coverage_location and not os.path.isfile(args.test_coverage_location):
        raise ValueError(
            f"test_coverage_location '{args.test_coverage_location}' does not exist."
        )

    print("Args Validated Successfully")


def run(args):
    validate_args(args)

    # In the case that a list of files have been given to run, split by comma
    # Then strip whitespace
    target_spec_list = args.target_spec.split(",")
    target_spec = args.target_spec
    if len(target_spec_list) == 1:
        target_spec = target_spec_list[0]
    else:
        for target in target_spec_list:
            target.strip()
        target_spec = target_spec_list

    spec_crawler = SpecCrawler(
        verbose=args.verbose,
        spec_dir=target_spec,
        enabled_extensions=set(args.spec_file_extensions.split(","))
        if args.spec_file_extensions
        else None,
    )

    # Initiate Spec Crawl to collect spec tags
    spec_tag_data = spec_crawler.run()

    # Check for specific testing framework support
    framework = None
    matches = None
    if args.test_framework:
        framework_exists = framework_support_check(args.test_framework)
        if not framework_exists:
            framework, matches = detect_framework(args.test_framework)

    if not args.test_framework:
        framework, matches = detect_framework(args.test_command)

    if framework:
        print(f"Framework detected: {framework}, with other matches: {matches}")
    else:
        print(
            "Failed to detect test framework, resorting to file-leve test granularity"
        )

    test_crawler = TestCrawler(
        verbose=args.verbose,
        test_dir=args.test_dir,
        enabled_extensions=set(args.test_extensions.split(","))
        if args.test_extensions
        else None,
        framework=framework,
    )

    # Run Test Crawl for test tags and test function signatures and line numbers
    test_tag_data = test_crawler.run()
    tag_coverage_data = test_crawler.get_coverage_data()

    # Checking for if the --target_spec arg is a list of files or a single spec file
    spec_subset_presence = False
    if type(target_spec) is list:
        spec_subset_presence = True
    if type(target_spec) is str:
        if not os.path.isdir(target_spec) and os.path.isfile(target_spec):
            spec_subset_presence = True

    if not spec_tag_data or not test_tag_data:
        print(
            "Warning, no spec data or tag data was missing after crawling, please double check your tags"
        )
        return 1

    linker = Linker(
        spec_data=spec_tag_data,
        test_data=test_tag_data,
        target_tag=args.target_tag,
        verbose=args.verbose,
        spec_subset=spec_subset_presence,
    )

    # Link up the test tag data and spec tag data while flagging invalid tags
    linked_data = linker.link_data()
    links = None
    invalid_tags = None
    if linked_data:
        links, invalid_tags = linked_data

    if args.tag_check:
        linker.display_invalid_tags()
        if invalid_tags:
            return 1
        else:
            return 0

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
            one_by_one=args.one_by_one,
            tag_coverage_data=tag_coverage_data,
            test_coverage_location=args.coverage_report_path,
            verbose=args.verbose,
        )
        generator.generate_report()

    if test_results:
        for _, result in test_results.items():
            if result["fail_count"] > 0:
                return 1
        return 0
    else:
        return 1

import argparse
import os
from spec_test_linker import Linker
from test_runner import Runner
from report_generation import Generator
from spec_test_crawler import SpecCrawler, TestCrawler

def validate_args(args):
    if not args.test_command:
        raise ValueError("test_command is required")
    if args.report and not args.report_output:
        raise ValueError("report_output is required when report is enabled")
    if args.report and args.report_type not in ["json", "html", "stdout"]:
        raise ValueError("Invalid report_type. Must be one of: json, html, stdout")
    if args.report and not os.path.isdir(args.report_output):
        raise ValueError(f"report_output '{args.report_output}' is not a valid directory")
    if args.target_spec and not os.path.exists(args.target_spec):
        raise ValueError(f"target_spec '{args.target_spec}' does not exist")
    if args.test_dir and not os.path.exists(args.test_dir):
        raise ValueError(f"test_dir '{args.test_dir}' does not exist")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_spec", default="features", help="Target dir/file/tag/list of files to read through")
    parser.add_argument("--spec_file_extensions", default=None, help="Comma-separated list of allowed spec file extensions")
    parser.add_argument("--test_dir", default="tests", help="Directory/file/test to read through")
    parser.add_argument("--test_command", help="Command to run the test")
    parser.add_argument("--test_extensions", default=None, help="Comma-separated list of allowed test file extensions")
    parser.add_argument("--report", help="Generate a report", action="store_true")
    parser.add_argument("--report_output", default=".", help="Directory to output the report")
    parser.add_argument("--report_type", default="json", help="Type of report to generate", choices=["json", "html", "stdout"])


    args = parser.parse_args()

    validate_args(args)
    print(f"Arguments: {args}")
    spec_crawler = SpecCrawler(args.target_spec, enabledExtensions=set(args.spec_file_extensions.split(',')) if args.spec_file_extensions else None)
    spec_tag_data = spec_crawler.run()

    test_crawler = TestCrawler(args.test_dir, enabledExtensions=set(args.test_extensions.split(',')) if args.test_extensions else None)
    test_tag_data = test_crawler.run()

    linker = Linker(spec_tag_data, test_tag_data)
    linker.link_data()
    linker.display_data()

if __name__ == "__main__":
    main()
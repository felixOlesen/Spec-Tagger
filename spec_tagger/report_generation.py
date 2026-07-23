import json
import os
import importlib.resources as pkg_resources


class Generator:
    """Report Generator
    We want the user to be able to generate a report of their tests after running spec tagger.
    """

    def __init__(
        self,
        report_output_dir: str,
        report_type: str,
        test_output: dict,
        invalid_tags: list,
        successful_links: dict,
        verbose: bool,
    ):
        self.report_output_dir = report_output_dir
        self.report_type = report_type
        self.test_output = test_output
        self.invalid_tags = invalid_tags
        self.successful_links = successful_links
        self.verbose = verbose
        self.output_object = {}

    def generate_report(self):
        self.construct_report_object()
        match self.report_type:
            case "json":
                self.generate_json()
            case "html":
                self.generate_html()
            case "stdout":
                self.generate_stdout()
            case _:
                print("Invalid report type given.")

    def construct_report_object(self):
        """Object Strucutre

        Test Results

            Spec item
                Line Number
                Spec snapshot
                Test Coverage
                Execution Time
                Passes
                    Coverage
                Failures
                    Output
                Error
                    Output

        Invalid Tags
            Tag
                Reason

        """
        self.output_object["test_results"] = self.test_output
        self.output_object["invalid_tags"] = self.invalid_tags
        for _, links in self.successful_links.items():
            full_tag = links["spec_tag"]["full_tag"]
            if full_tag in self.output_object["test_results"]:
                self.output_object["test_results"][full_tag]["links"] = links
            else:
                print("Warning, links found with no connected test results.")

        if self.verbose:
            print("Constructed Report Object:")
            print(self.output_object)

    def generate_json(self):
        location = os.path.join(self.report_output_dir, "report.json")
        with open(location, "w") as f:
            json.dump(self.output_object, f)

    def generate_html(self):
        pass

    def generate_stdout(self):
        pass

    def _copy_template_file(self, file_name):
        pass

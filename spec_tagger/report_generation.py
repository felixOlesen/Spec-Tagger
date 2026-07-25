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
        test_output: dict | None,
        invalid_tags: list | None,
        successful_links: dict | None,
        verbose: bool,
    ):
        self.report_output_dir = report_output_dir
        self.report_type = report_type
        self.test_output = test_output
        self.invalid_tags = invalid_tags
        self.successful_links = successful_links
        self.verbose = verbose
        self.output_object = {}
        self.report_name = "report.json"

    def generate_report(self):
        self._construct_report_object()
        match self.report_type:
            case "json":
                self._generate_json()
            case "html":
                self._generate_html()
            case "stdout":
                self._generate_stdout()
            case _:
                print("Invalid report type given.")

    def _construct_report_object(self):
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
        if not self.successful_links:
            print("Warning tag links found to be null on report generation.")
            return

        if not self.test_output:
            print("Warning test_output found to be null on test generation")
            return

        self.output_object["test_results"] = self.test_output
        self.output_object["invalid_tags"] = self.invalid_tags

        for _, links in self.successful_links.items():
            full_tag = links["spec_tag"]["full_tag"]
            if full_tag in self.output_object["test_results"]:
                self.output_object["test_results"][full_tag]["spec_tag"] = links[
                    "spec_tag"
                ]
                self.output_object["test_results"][full_tag]["test_tags"] = links[
                    "test_tags"
                ]
            else:
                print("Warning, links found with no connected test results.")

        if self.verbose:
            print("Constructed Report Object:")
            print(self.output_object)

    def _generate_json(self):
        location = os.path.join(self.report_output_dir, self.report_name)
        with open(location, "w") as f:
            json.dump(self.output_object, f)

    def _generate_html(self):
        os.makedirs(self.report_output_dir, exist_ok=True)

        location = os.path.join(self.report_output_dir, "data.js")
        with open(location, "w") as f:
            f.write(f"window.REPORT_DATA = {json.dumps(self.output_object)};")

        self._copy_template_file("index.html")
        self._copy_template_file("style.css")
        self._copy_template_file("script.js")

        print(f"Report successfully saved to {os.path.abspath(self.report_output_dir)}")

    def _generate_stdout(self):
        pass

    def _copy_template_file(self, file_name):
        template_content = (
            pkg_resources.files("spec_tagger.templates").joinpath(file_name).read_text()
        )

        destination = os.path.join(self.report_output_dir, file_name)
        with open(destination, "w", encoding="utf-8") as f:
            f.write(template_content)

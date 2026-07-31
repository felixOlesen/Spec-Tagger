import os
import re
from spec_tagger.language_patterns import FRAMEWORKS
from spec_tagger.spec_test_data import TagData, SpecTagData, TestTagData


class Crawler:
    def __init__(self, verbose, directory_or_files):
        self.directory_or_files = directory_or_files
        self.verbose = verbose
        self.files = []
        self.tag_data = TagData()
        # self.tag_data = []
        self.enabled_extensions = []  # This will be set in subclasses
        # Tag Regex should match to the format:
        # [feat or story or step]~[FEATURE NAME]~[REVISION NUMBER]
        # Example Tag: feat~MyFeature~1
        self.tag_regex = re.compile(
            r"(?<![A-Za-z0-9_~])(feat|story|step)~([A-Za-z0-9_]+)~([0-9]+)(?![A-Za-z0-9_~])"
        )

    def run(self):
        self.crawl_files()
        if not self.files:
            print("No files found. Exiting.")
            return

        self.extract_tags()

        return self.tag_data

    def crawl_files(self):

        found_files = []
        if type(self.directory_or_files) is str and os.path.isdir(
            self.directory_or_files
        ):
            for root, _, files in os.walk(self.directory_or_files):
                for file in files:
                    if any(file.endswith(ext) for ext in self.enabled_extensions):
                        found_files.append(os.path.join(root, file))

        if found_files and self.verbose:
            print(f"Files have been found:\n{found_files}")

        self.files = found_files

    def extract_tags(self):
        for file in self.files:
            with open(file, "r", encoding="utf-8-sig") as f:
                for line_num, line in enumerate(f, start=1):
                    if "~" not in line:
                        continue
                    m = self.tag_regex.search(line.rstrip())
                    stripped = line.rstrip()
                    matches = list(self.tag_regex.finditer(stripped))
                    for m in matches:
                        tag_type, name, revision = m.groups()
                        full_tag = m.group(0)
                        closing_line = None
                        if tag_type == "step":
                            closing_line = line_num

                        self.tag_data.add_tag(
                            filename=file,
                            line=line_num,
                            closing_line=closing_line,
                            tag_type=tag_type,
                            name=name,
                            revision=revision,
                            full_tag=full_tag,
                            content=None,
                            item_start_line=line_num,
                        )
        if self.verbose:
            for file, tags in self.tag_data.file_to_tag.items():
                if len(tags) > 0:
                    print(f"Found tags in {file}")


class TestCrawler(Crawler):
    def __init__(self, verbose, test_dir, enabled_extensions=None, framework=None):
        super().__init__(verbose, test_dir)
        self.enabled_extensions = enabled_extensions or {
            ".py",
            ".js",
            ".java",
            ".cpp",
            ".cs",
            ".rb",
            ".go",
            ".ts",
            ".php",
            ".swift",
            ".kt",
            ".m",
            ".scala",
            ".sh",
            ".pl",
            ".r",
            ".lua",
            ".hs",
            ".erl",
            ".ex",
            ".exs",
        }
        self.framework = framework
        self.tag_data = TestTagData()

    def run(self):
        self.crawl_files()
        if not self.files:
            if self.verbose:
                print("No files found. Exiting.")
            return None

        self.extract_tags()
        if self.framework:
            self.extract_and_assign_test_declarations()
        return self.tag_data

    def extract_and_assign_test_declarations(self):
        # get mapping of filenames to tag data
        LINE_STOP_CONDITION = 20  # Number of lines to go across before giving up
        file_to_tag = self.tag_data.file_to_tag
        if not self.framework:
            print("Warning, exited due to null framework test function extraction.")
            return

        FW_INFO = FRAMEWORKS[self.framework]
        func_pattern = FW_INFO.get("func")
        describe_pattern = FW_INFO.get("describe")
        example_pattern = FW_INFO.get("example")
        skip_prefixes = FW_INFO["skip_prefixes"]

        # loop through the files and being crawling after each line number to identify test function signatures
        for filename, tags in file_to_tag.items():
            _, fileExtension = os.path.splitext(filename)
            if fileExtension not in FW_INFO["extensions"]:
                continue

            # find function signatures if that granularity is supported, otherwise, stick to file-level granularity
            # if 'test_function' key is not present in tag, assum file-level, if it is but it's None, assume tag invalidity
            with open(filename, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()

            line_cache = {}

            for tag in tags:
                if tag["line"] in line_cache:
                    tag["test_function"], tag["item_start_line"] = line_cache[
                        tag["line"]
                    ]
                    continue

                found, found_at = None, None
                start = tag["line"]
                # tag['line'] is 1-based
                for offset, line in enumerate(
                    lines[start : start + LINE_STOP_CONDITION]
                ):
                    stripped = line.strip()
                    if not stripped or stripped.startswith(skip_prefixes):
                        continue

                    if describe_pattern and example_pattern:
                        m = example_pattern.match(line)
                        if m:
                            desc = m.group(1)
                            path = self._describe_path(
                                lines, start + offset, describe_pattern
                            )
                            found = " > ".join(path + [desc])
                            found_at = start + offset + 1
                            break
                        if describe_pattern.match(line):
                            continue
                    elif func_pattern is not None:
                        m = func_pattern.match(line)
                        if m:
                            found = next((g for g in m.groups() if g is not None), None)
                            found_at = start + offset + 1
                            break
                    break

                tag["test_function"] = found  # None means invalid tag
                tag["item_start_line"] = found_at
                line_cache[tag["line"]] = (found, found_at)

                if self.verbose:
                    print(f"Test Function found: {found}\nAt: {filename}:{found_at}")

    def _describe_path(self, lines, example_idx, describe_pattern):
        """Collect enclosing describe descriptions above `example_idx`, using
        indentation as the nesting proxy. Returns outermost-first."""
        path = []
        example_indent = len(lines[example_idx]) - len(lines[example_idx].lstrip())
        current = example_indent

        for i in range(example_idx - 1, -1, -1):
            line = lines[i]
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            if indent >= current:
                continue  # sibling or deeper: not an ancestor
            m = describe_pattern.match(line)
            if m:
                path.append(m.group(1).strip("\"'"))
                current = indent
                if indent == 0:
                    break
        return list(reversed(path))


class SpecCrawler(Crawler):
    # Can be a directory, list of files, single file, or specific tag.
    def __init__(self, verbose, spec_dir, enabled_extensions=None):
        super().__init__(verbose, spec_dir)
        self.enabled_extensions = {".spec", ".feature", ".md", ".txt"}
        if enabled_extensions:
            self.enabled_extensions.update(enabled_extensions)
        self.tag_data = SpecTagData()

    def crawl_files(self):
        # Logic to crawl through the spec_dir and find spec files with enabled extensions.
        found_files = []
        # If spec_dir is a directory, walk through it
        if type(self.directory_or_files) is str and os.path.isdir(
            self.directory_or_files
        ):
            for root, _, files in os.walk(self.directory_or_files):
                for file in files:
                    if any(file.endswith(ext) for ext in self.enabled_extensions):
                        found_files.append(os.path.join(root, file))
        # If spec_dir is a list of files
        elif type(self.directory_or_files) is list:
            for file in self.directory_or_files:
                if os.path.isfile(file) and any(
                    file.endswith(ext) for ext in self.enabled_extensions
                ):
                    found_files.append(file)
        # If spec_dir is a single file
        elif type(self.directory_or_files) is str and os.path.isfile(
            self.directory_or_files
        ):
            if any(
                self.directory_or_files.endswith(ext) for ext in self.enabled_extensions
            ):
                found_files.append(self.directory_or_files)

        if type(self.directory_or_files) is list and len(
            self.directory_or_files
        ) != len(found_files):
            missing_files = set(self.directory_or_files) - set(found_files)
            print(
                f"Warning: The following specified files were not found or do not have enabled extensions: {missing_files}, continuing with the found files."
            )
        if found_files and self.verbose:
            print(f"Files have been found:\n{found_files}")

        self.files = found_files

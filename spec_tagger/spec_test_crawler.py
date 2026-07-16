
import os
import re
from spec_tagger.language_patterns import FUNC_PATTERNS, SKIP_PREFIXES
class Crawler:
    def __init__(self, verbose, directory_or_files):
        self.directory_or_files = directory_or_files
        self.verbose = verbose
        self.files = []
        self.tag_data = []
        self.enabled_extensions = None  # This will be set in subclasses
        # Tag Regex should match to the format:
        # [feat or story or step]~[FEATURE NAME]~[REVISION NUMBER]
        # Example Tag: feat~MyFeature~1
        self.tag_regex = re.compile(r'(?<![A-Za-z0-9_~])(feat|story|step)~([A-Za-z0-9_]+)~([0-9]+)(?![A-Za-z0-9_~])')
    
    def run(self):
        self.crawl_files()
        if not self.files:
            print("No files found. Exiting.")
            return
        
        self.extract_tags()

        return self.tag_data

    def crawl_files(self):

        found_files = []
        if type(self.directory_or_files) is str and os.path.isdir(self.directory_or_files):
            for root, dirs, files in os.walk(self.directory_or_files):
                for file in files:
                    if any(file.endswith(ext) for ext in self.enabled_extensions):
                        found_files.append(os.path.join(root, file))

        self.files = found_files

    def extract_tags(self):
        self.tag_data = []
        for file in self.files:
            with open(file, 'r', encoding='utf-8-sig') as f:
                file_tags = []
                for line_num, line in enumerate(f, start=1):
                    if '~' not in line:
                        continue
                    m = self.tag_regex.search(line.rstrip())
                    stripped = line.rstrip()
                    matches = list(self.tag_regex.finditer(stripped))
                    for m in matches:
                        tag_type, name, revision = m.groups()
                        full_tag = m.group(0)
                        file_tags.append({'filename': file, 'line': line_num, 'type': tag_type, 'name': name, 'revision': revision, 'full_tag': full_tag})
                    
                if file_tags:
                    self.tag_data.extend(file_tags)
                    if self.verbose:
                        print(f"Found tags in {file}")
                else:
                    if self.verbose:
                        print(f"No tags found in {file}.")

class TestCrawler(Crawler):
    def __init__(self, verbose, test_dir, enabled_extensions=None):
        super().__init__(verbose, test_dir)
        self.enabled_extensions = enabled_extensions or {'.py', '.js', '.java', '.cpp', '.cs', '.rb', '.go', '.ts', '.php', '.swift', '.kt', '.m', '.scala', '.sh', '.pl', '.r', '.lua', '.hs', '.erl', '.ex', '.exs'}

    def run(self):
        self.crawl_files()
        if not self.files:
            if self.verbose:
                print("No files found. Exiting.")
            return
        
        self.extract_tags()
        self.extract_and_assign_test_declarations()
        return self.tag_data

    def extract_and_assign_test_declarations(self):
        # get mapping of filenames to tag data 
        LINE_STOP_CONDITION = 100 # Number of lines to go across before giving up
        file_to_tag = {}
        for tag in self.tag_data:
            if tag['filename'] not in file_to_tag:
                file_to_tag[tag['filename']] = []
            file_to_tag[tag['filename']].append(tag)
        
        # loop through the files and being crawling after each line number to identify test function signatures
        for filename, tags in file_to_tag.items():
            _, fileExtension = os.path.splitext(filename)
            lineToTestSig = {}
            
            # find function signatures if that granularity is supported, otherwise, stick to file-level granularity
            # if 'test_function' key is not present in tag, assum file-level, if it is but it's None, assume tag invalidity
            if fileExtension in FUNC_PATTERNS:
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                func_pattern = FUNC_PATTERNS[fileExtension]
                skip_pattern = SKIP_PREFIXES[fileExtension]

                for tag in tags:
                    if tag['line'] in lineToTestSig:
                        tag['test_function'] = lineToTestSig[tag['line']]
                        continue

                    found = None
                    # tag['line'] is 1-based
                    for line in lines[tag['line'] : tag['line'] + LINE_STOP_CONDITION]:
                        stripped = line.strip()
                        if not stripped:
                            continue
                        m = func_pattern.match(line)
                        if m:
                            found = next((g for g in m.groups() if g is not None), None)
                            break
                        if stripped.startswith(skip_pattern):
                            continue
                        break  

                    tag['test_function'] = found          # None means invalid tag
                    lineToTestSig[tag['line']] = found
                            

                                    
class SpecCrawler(Crawler):
    # Can be a directory, list of files, single file, or specific tag.
    def __init__(self, verbose, spec_dir, enabled_extensions=None):
        super().__init__(verbose, spec_dir)
        self.enabled_extensions = {'.spec', '.feature', '.md', '.txt', '.allium'}
        if enabled_extensions:
            self.enabled_extensions.update(enabled_extensions)

    def crawl_files(self):
        # Logic to crawl through the spec_dir and find spec files with enabled extensions.
        found_files = []
        # If spec_dir is a directory, walk through it
        if type(self.directory_or_files) is str and os.path.isdir(self.directory_or_files):
            for root, dirs, files in os.walk(self.directory_or_files):
                for file in files:
                    if any(file.endswith(ext) for ext in self.enabled_extensions):
                        found_files.append(os.path.join(root, file))
        # If spec_dir is a list of files
        elif type(self.directory_or_files) is list:
            for file in self.directory_or_files:
                if os.path.isfile(file) and any(file.endswith(ext) for ext in self.enabled_extensions):
                    found_files.append(file)
        # If spec_dir is a single file
        elif type(self.directory_or_files) is str and os.path.isfile(self.directory_or_files):
            if any(self.directory_or_files.endswith(ext) for ext in self.enabled_extensions):
                found_files.append(self.directory_or_files)
        
        if type(self.directory_or_files) is list and len(self.directory_or_files) != len(found_files):
            missing_files = set(self.directory_or_files) - set(found_files)
            print(f"Warning: The following specified files were not found or do not have enabled extensions: {missing_files}, continuing with the found files.")
        
        self.files = found_files
    
    
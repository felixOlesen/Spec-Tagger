
import os
import re
import itertools
from language_patterns import FUNC_PATTERNS, SKIP_PREFIXES
class Crawler:
    def __init__(self, directoryOrFiles):
        self.directoryOrFiles = directoryOrFiles
        self.files = []
        self.tagData = []
        self.enabledExtensions = None  # This will be set in subclasses
        # Tag Regex should match to the format:
        # [feat or story or step]~[FEATURE NAME]~[REVISION NUMBER]
        # Example Tag: feat~MyFeature~1
        self.tagRegex = re.compile(r'(?<![A-Za-z0-9_~])(feat|story|step)~([A-Za-z0-9_]+)~([0-9]+)(?![A-Za-z0-9_~])')
    
    def run(self):
        self.crawlFiles()
        if not self.files:
            print("No files found. Exiting.")
            return
        
        self.extractTags()

        return self.tagData

    def crawlFiles(self):

        found_files = []
        if type(self.directoryOrFiles) is str and os.path.isdir(self.directoryOrFiles):
            for root, dirs, files in os.walk(self.directoryOrFiles):
                for file in files:
                    if any(file.endswith(ext) for ext in self.enabledExtensions):
                        found_files.append(os.path.join(root, file))

        self.files = found_files

    def extractTags(self):
        self.tagData = []
        for file in self.files:
            with open(file, 'r', encoding='utf-8-sig') as f:
                file_tags = []
                for line_num, line in enumerate(f, start=1):
                    if '~' not in line:
                        continue
                    m = self.tagRegex.search(line.rstrip())
                    stripped = line.rstrip()
                    matches = list(self.tagRegex.finditer(stripped))
                    for m in matches:
                        tag_type, name, revision = m.groups()
                        full_tag = m.group(0)
                        file_tags.append({'filename': file, 'line': line_num, 'type': tag_type, 'name': name, 'revision': revision, 'full_tag': full_tag})
                    
                if file_tags:
                    self.tagData.extend(file_tags)
                    print(f"Found tags in {file}")
                else:
                    print(f"No tags found in {file}.")

class TestCrawler(Crawler):
    def __init__(self, testDir, enabledExtensions=None):
        super().__init__(testDir)
        self.enabledExtensions = enabledExtensions or {'.py', '.js', '.java', '.cpp', '.cs', '.rb', '.go', '.ts', '.php', '.swift', '.kt', '.m', '.scala', '.sh', '.pl', '.r', '.lua', '.hs', '.erl', '.ex', '.exs'}

    def run(self):
        self.crawlFiles()
        if not self.files:
            print("No files found. Exiting.")
            return
        
        self.extractTags()
        self.extract_and_assign_test_declarations()
        return self.tagData

    def extract_and_assign_test_declarations(self):
        # get mapping of filenames to tag data 
        LINE_STOP_CONDITION = 100 # Number of lines to go across before giving up
        fileToTag = {}
        for tag in self.tagData:
            if tag['filename'] not in fileToTag:
                fileToTag[tag['filename']] = []
            fileToTag[tag['filename']].append(tag)
        
        # loop through the files and being crawling after each line number to identify test function signatures
        for filename, tags in fileToTag.items():
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
    def __init__(self, specDir, enabledExtensions=None):
        super().__init__(specDir)
        self.enabledExtensions = {'.spec', '.feature', '.md', '.txt', '.allium'}
        if enabledExtensions:
            self.enabledExtensions.update(enabledExtensions)

    def crawlFiles(self):
        # Logic to crawl through the specDir and find spec files with enabled extensions.
        found_files = []
        # If specDir is a directory, walk through it
        if type(self.directoryOrFiles) is str and os.path.isdir(self.directoryOrFiles):
            for root, dirs, files in os.walk(self.directoryOrFiles):
                for file in files:
                    if any(file.endswith(ext) for ext in self.enabledExtensions):
                        found_files.append(os.path.join(root, file))
        # If specDir is a list of files
        elif type(self.directoryOrFiles) is list:
            for file in self.directoryOrFiles:
                if os.path.isfile(file) and any(file.endswith(ext) for ext in self.enabledExtensions):
                    found_files.append(file)
        # If specDir is a single file
        elif type(self.directoryOrFiles) is str and os.path.isfile(self.directoryOrFiles):
            if any(self.directoryOrFiles.endswith(ext) for ext in self.enabledExtensions):
                found_files.append(self.directoryOrFiles)
        
        if type(self.directoryOrFiles) is list and len(self.directoryOrFiles) != len(found_files):
            missing_files = set(self.directoryOrFiles) - set(found_files)
            print(f"Warning: The following specified files were not found or do not have enabled extensions: {missing_files}, continuing with the found files.")
        
        self.files = found_files
    
    
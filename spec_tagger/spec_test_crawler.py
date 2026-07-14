
import os
import re

class TestCrawler:
    def __init__(self):
        pass


class SpecCrawler:
    # Can be a directory, list of files, single file, or specific tag.
    enabledExtensions = {'.spec', '.feature', '.md', '.txt', '.allium'}
    
    # Tag Regex should match to the format:
    # [feat or story or step]~[FEATURE NAME]~[REVISION NUMBER]
    # Example Tag: feat~MyFeature~1
    tagRegex = re.compile(r'(?<![A-Za-z0-9_~])(feat|story|step)~([A-Za-z0-9_]+)~([0-9]+)$')

    def __init__(self, specDir, enabledExtensions=None):
        self.specDir = specDir
        print(f"SpecCrawler initialized with specDir: {specDir}")
        if enabledExtensions:
            print(f"Enabled extensions provided: {enabledExtensions}")
            self.enabledExtensions.update(enabledExtensions)
        
        self.tagData = []
        self.files = []

    def run(self):
        self.crawlFiles()
        if not self.files:
            print("No spec files found. Exiting.")
            return
        
        self.extractTags()

        return self.tagData

    def crawlFiles(self):
        # Logic to crawl through the specDir and find spec files with enabled extensions.
        found_files = []
        # If specDir is a directory, walk through it and yield files with enabled extensions.
        if type(self.specDir) is str and os.path.isdir(self.specDir):
            for root, dirs, files in os.walk(self.specDir):
                for file in files:
                    if any(file.endswith(ext) for ext in self.enabledExtensions):
                        found_files.append(os.path.join(root, file))
        # If specDir is a list of files, yield those that have enabled extensions.
        elif type(self.specDir) is list:
            for file in self.specDir:
                if os.path.isfile(file) and any(file.endswith(ext) for ext in self.enabledExtensions):
                    found_files.append(file)
        # If specDir is a single file, yield it if it has an enabled extension.
        elif type(self.specDir) is str and os.path.isfile(self.specDir):
            if any(self.specDir.endswith(ext) for ext in self.enabledExtensions):
                found_files.append(self.specDir)
        
        print(f"Found spec files: {found_files}")

        if type(self.specDir) is list and len(self.specDir) != len(found_files):
            missing_files = set(self.specDir) - set(found_files)
            print(f"Warning: The following specified files were not found or do not have enabled extensions: {missing_files}, continuing with the found files.")
        
        self.files = found_files
    
    def extractTags(self):
        for file in self.files:
            with open(file, 'r', encoding='utf-8-sig') as f:
                file_tags = []
                for line_num, line in enumerate(f, start=1):
                    if '~' not in line:
                        continue
                    m = self.tagRegex.search(line.rstrip())
                    if m:
                        tag_type, name, revision = m.groups()
                        file_tags.append({'filename': file, 'line': line_num, 'type': tag_type, 'name': name, 'revision': revision})
                if file_tags:
                    self.tagData.extend(file_tags)
                    print(f"Found tags in {file}: {file_tags}")
                else:
                    print(f"No tags found in {file}.")
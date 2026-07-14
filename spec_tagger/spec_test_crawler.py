
import os
import re

class TestCrawler:
    def __init__(self):
        pass


class SpecCrawler:
    # Can be a directory, list of files, single file, or specific tag.
    specDir = None
    enabledExtensions = {'.spec', '.feature', '.md', '.txt', '.allium'}
    tags = []
    # Tag Regex should match to the format:
    # - specTagger~[feat or story or step]~[FEATURE NAME]~[REVISION NUMBER]
    tagRegex = re.compile(r'^specTagger~(feat|story|step)~[A-Za-z0-9_]+~[0-9]+$')

    def __init__(self, specDir, enabledExtensions=None):
        self.specDir = specDir
        print(f"SpecCrawler initialized with specDir: {specDir}")
        if enabledExtensions:
            print(f"Enabled extensions provided: {enabledExtensions}")
            self.enabledExtensions.update(enabledExtensions)
        
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
''' language_patterns.py: 
        Based on the crawled file extension, a specific regex pattern is used to identify function signatures.
        When traversing lines, patterns for skipping lines are also identified (comments and decorators)
        
        A key distinction also needs to be made between programming languages that have unique function names (e.g. python, rust, java)
        versus languages that test using description-based signatures like with the JEST test framework.
'''

import re

FUNC_PATTERNS = {
    '.py': re.compile(r'^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)'),
    '.rb': re.compile(r'^\s*def\s+(?:self\.)?([A-Za-z_]\w*[?!]?)')
}

SKIP_PREFIXES = {
    '.py': ('#', '@'),
    '.rb': ('#',),
}


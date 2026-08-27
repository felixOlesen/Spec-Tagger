import re
from tree_sitter import Query, QueryCursor
from tree_sitter_language_pack import get_language, get_parser
from spec_tagger.merge_analysis.language_support import (
    QUERIES,
    PYTHON_STOPWORDS,
    RUBY_STOPWORDS,
    EXT_TO_LANG,
)
from functools import lru_cache


class SymbolExtractor:
    def __init__(self) -> None:
        # For splitting camel case and snake case signatures
        self._SPLIT = re.compile(r"[_\-.]|(?<=[a-z0-9])(?=[A-Z])")

        # For comparing words
        self._WORD = re.compile(r"[A-Za-z]{3,}")

    @lru_cache(maxsize=8)
    def _compiled(self, language: str) -> Query:
        return Query(get_language(language), QUERIES[language])

    def _split_identifier(self, name: str) -> set[str]:
        return {
            p.lower()
            for p in self._SPLIT.split(name)
            if len(p) >= 3 and p.lower() not in RUBY_STOPWORDS
        }

    def _prose_words(self, text: str) -> set[str]:
        return {w.lower() for w in self._WORD.findall(text)} - RUBY_STOPWORDS

    def tree_sitter_code_symbols(
        self, source: str, changed_lines: set[int], language: str
    ):
        if language not in QUERIES or not changed_lines:
            return set()

        tree = get_parser(language).parse(source.encode())

        out: set[str] = set()
        for _, caps in QueryCursor(self._compiled(language)).matches(tree.root_node):
            for kind, nodes in caps.items():
                for node in nodes:
                    line = node.start_point[0] + 1

                    if line not in changed_lines:
                        continue
                    raw = node.text
                    if raw is None:
                        continue
                    text = raw.decode(errors="replace")
                    out |= (
                        self._split_identifier(text)
                        if kind == "sym"
                        else (
                            {w.lower() for w in self._WORD.findall(text)}
                            - RUBY_STOPWORDS
                        )
                    )
        return out

    def relatedness_test(
        self, spec_text: str, code_source: str, changed_lines: set[int], language: str
    ) -> float:
        a = self._prose_words(spec_text)
        b = self.tree_sitter_code_symbols(code_source, changed_lines, language)
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def relatedness_code_to_code(
        self,
        test_code_symbols: set[str],
        src_code_symbols: set[str],
    ) -> float:
        if not test_code_symbols or not src_code_symbols:
            return 0.0
        return len(test_code_symbols & src_code_symbols) / len(
            test_code_symbols | src_code_symbols
        )

    def relatedness_spec_to_code(self, spec_text: str, code_source: set[str]) -> float:
        a = self._prose_words(spec_text)
        b = code_source
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def relatedness_spec_to_spec(self, spec_text: str, comp_spec_text: str) -> float:
        a = self._prose_words(spec_text)
        b = self._prose_words(comp_spec_text)
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

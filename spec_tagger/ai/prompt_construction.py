from spec_tagger.spec_review.solution import Solution


class PromptConstructor:
    def __init__(self, solutions: list[Solution]) -> None:
        self.solutions = solutions

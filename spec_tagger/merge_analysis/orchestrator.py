from spec_tagger.merge_analysis.change_search import ChangeSearch
from spec_tagger.merge_analysis.case_construction import CaseConstructor


def validate_args(args):
    pass


def run(args):
    # PROCESS
    # Classification of git logs
    # - Identify changes where only the spec is updated,
    #   or where only the spec is updated, or where only
    #   the implementation code is updated. But where the
    #   connecting items are updated at a later date.
    #
    #   Parse the git logs from this command:
    #   git log --format='COMMIT %H' --name-only --merges $START..HEAD
    #
    #   Then find out which artifacts are touched based on the path prefix they have
    #   (features/ , tests/ , src/)

    search = ChangeSearch(args.spec_dir, args.test_dir, args.src_dir)
    complete_matrices, commit_times = search.run()

    constructor = CaseConstructor(
        complete_matrices,
        args.case_dir,
        args.repo_abs_path,
        args.spec_dir,
        args.test_dir,
        args.src_dir,
        commit_times,
    )
    constructor.run()
